import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='a'
)

PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_STATUS_DICT = {
    'approved':
    'Ревьюеру всё понравилось, можно приступать к следующему уроку.',
    'rejected':
    'К сожалению в работе нашлись ошибки.',
    'reviewing':
    'Работу взяли на проверку.'
}


bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None or homework_status is None:
        error_message = f'Имя или статус работы отсутствуют: {homework}'
        logging.error(error_message)
        return error_message
    if homework_status in HOMEWORK_STATUS_DICT:
        verdict = HOMEWORK_STATUS_DICT[homework_status]
    else:
        error_message = f'Неверный статус работы: {homework_status}'
        logging.error(error_message)
        return error_message
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    try:
        headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
        params = {'from_date': current_timestamp}
        homework_statuses = requests.get(URL, params=params, headers=headers)
        return homework_statuses.json()
    except requests.RequestException as e:
        error_message = f'Статус не получен: {e}'
        logging.error(error_message)
        send_message(error_message, bot)
        time.sleep(5)
        return {}


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logging.debug('Бот запущен')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot
                )
            logging.info('Сообщение отправлено.')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            error_message = f'Бот столкнулся с ошибкой: {e}'
            logging.error(error_message)
            send_message(error_message, bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
