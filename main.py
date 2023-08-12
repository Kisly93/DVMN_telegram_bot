import requests
import os
import telegram
from dotenv import load_dotenv
import time
import textwrap


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
            print("Интернет соединение отсутствует. Повторная попытка через 20 секунд...")
            time.sleep(20)


if __name__ == '__main__':
    main()
