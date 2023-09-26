import logging
import os
import textwrap
import time
import traceback

import requests
import telegram
from dotenv import load_dotenv


class TelegramLogHandler(logging.Handler):
    def __init__(self, bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.bot = bot

    def emit(self, record):
        log_message = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=log_message)


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
    load_dotenv()
    chat_id = os.getenv('CHAT_ID_TG')
    telegram_token = os.getenv('TOKEN_TELEGRAM')
    dwmn_token = os.getenv('DWMN_TOKEN')
    bot = telegram.Bot(token=telegram_token)
    bot.logger.addHandler(TelegramLogHandler(bot, chat_id))
    bot.logger.warning('Бот запущен')
    last_timestamp = None
    while True:
        try:
            url = 'https://dvmn.org/api/long_polling/'
            headers = {"Authorization": dwmn_token}
            params = {'timestamp': last_timestamp}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            lesson_reviews = response.json()

            if lesson_reviews['status'] == 'timeout':
                last_timestamp = lesson_reviews['timestamp_to_request']
            else:
                last_timestamp = lesson_reviews['last_attempt_timestamp']
                new_attempts = lesson_reviews['new_attempts']
                for new_attempt in new_attempts:
                    lesson_title = new_attempt['lesson_title']
                    is_negative = new_attempt['is_negative']
                    lesson_url = new_attempt['lesson_url']
                    send_telegram_notification(lesson_title, is_negative, lesson_url, chat_id, bot)

        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.ConnectionError:
            error_message = "Интернет соединение отсутствует. Повторная попытка через 20 секунд..."
            bot.logger.warning(error_message)
            time.sleep(20)
        except Exception as e:
            error_message = f"Бот упал с ошибкой: {str(e)}\n\n{traceback.format_exc()}"
            bot.logger.warning(error_message)


if __name__ == '__main__':
    main()
