import requests
import os
import telegram
from dotenv import load_dotenv

load_dotenv()
chat_id = os.getenv('CHAT_ID_TG')
telegram_token = os.getenv('TOKEN_TELEGRAM')
dwmn_token = os.getenv('DWMN_TOKEN')
bot = telegram.Bot(token=telegram_token)


def send_telegram_notification(lesson_title, is_negative, lesson_url):
    if not is_negative:
        result_message = "Преподавателю все понравилось, можно приступать к следущему уроку!"
    else:
        result_message = "К сожалению, в работе нашлись ошибки."
    message = (
        f"У вас проверили работу {lesson_title}\n"
        f"{result_message}\n"
        f"Ссылка на урок: {lesson_url}"
    )
    bot.send_message(chat_id=chat_id, text=message)


def get_answer():
    last_timestamp = None
    while True:
        url = 'https://dvmn.org/api/long_polling/'
        headers = {
            "Authorization": dwmn_token
        }
        try:
            params = {}
            if last_timestamp:
                params['timestamp'] = last_timestamp

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if 'new_attempts' in data and data['new_attempts']:
                for new_attempt in data['new_attempts']:
                    lesson_title = new_attempt['lesson_title']
                    is_negative = new_attempt['is_negative']
                    lesson_url = new_attempt['lesson_url']
                    send_telegram_notification(lesson_title, is_negative, lesson_url)


        except requests.exceptions.Timeout:
            print("Сервер не отвечает")
        except requests.exceptions.ConnectionError:
            print("Интернет соединение отсутствует")


def main():
    get_answer()


if __name__ == '__main__':
    main()
