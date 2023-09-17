import logging
import os
import textwrap
import time
import traceback

import requests
import telegram
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_file_handler = logging.FileHandler(f"{__name__}.log", mode='a')
log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

log_file_handler.setFormatter(log_formatter)
logger.addHandler(log_file_handler)


def log_to_chat_and_file(message, chat_id, bot):
    bot.send_message(chat_id=chat_id, text=message)
    logger.info(message)


def send_telegram_notification(lesson_title, is_negative, lesson_url, chat_id, bot):
    if not is_negative:
        result_message = "Преподавателю все понравилось, можно приступать к следущему уроку!"
    else:
        result_message = "К сожалению, в работе нашлись ошибки."
    message = textwrap.dedent(f"""
            У вас проверили работу {lesson_title}
            {result_message}
            Ссылка на урок: {lesson_url}
                    """)
    bot.send_message(chat_id=chat_id, text=message)


def main():
    while True:
        try:
            load_dotenv()
            chat_id = os.getenv('CHAT_ID_TG')
            telegram_token = os.getenv('TOKEN_TELEGRAM')
            dwmn_token = os.getenv('DWMN_TOKEN')
            bot = telegram.Bot(token=telegram_token)
            log_message = "Бот запущен"
            log_to_chat_and_file(log_message, chat_id, bot)
            last_timestamp = None
            while True:
                url = 'https://dvmn.org/api/long_polling/'
                headers = {
                    "Authorization": dwmn_token
                }
                try:
                    params = {'timestamp': last_timestamp}
                    response = requests.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    dvmn_api_data = response.json()

                    if dvmn_api_data['status'] == 'timeout':
                        last_timestamp = dvmn_api_data['timestamp_to_request']
                    else:
                        last_timestamp = dvmn_api_data['last_attempt_timestamp']
                        new_attempts = dvmn_api_data['new_attempts']
                        for new_attempt in new_attempts:
                            lesson_title = new_attempt['lesson_title']
                            is_negative = new_attempt['is_negative']
                            lesson_url = new_attempt['lesson_url']
                            send_telegram_notification(lesson_title, is_negative, lesson_url, chat_id, bot)

                except requests.exceptions.Timeout:
                    pass
                except requests.exceptions.ConnectionError:
                    error_message = "Интернет соединение отсутствует. Повторная попытка через 20 секунд..."
                    log_to_chat_and_file(error_message, chat_id, bot)
                    time.sleep(20)
        except Exception as e:
            error_message = f"Бот упал с ошибкой: {str(e)}\n\n{traceback.format_exc()}"
            log_to_chat_and_file(error_message, chat_id, bot)


if __name__ == '__main__':
    main()
