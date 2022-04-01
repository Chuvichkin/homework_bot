import os
import requests
import time
import logging
from dotenv import load_dotenv
from requests import RequestException
from telegram import Bot
from http import HTTPStatus
from exceptions import APIAnswerInvalidException, APIWrongStatusException, MissingTokenException

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    filemode="a",
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
PAYLOAD = {'from_date': 0}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в чат телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Сообщение отправлено! Текст сообщения: {message}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения {error}')
        raise Exception(error)


def get_api_answer(current_timestamp):
    """Получаем ответ API."""
    params = {'from_date': current_timestamp}
    homework = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework.status_code != HTTPStatus.OK:
        error_message = 'Ошибка! API не вернул корректный статус.'
        logging.error(error_message)
        raise APIAnswerInvalidException(error_message)
    try:
        response = homework.json()
    except Exception as error:
        logging.error(f'Нет ответа от сервера {error}')
        raise Exception(error)
    return response


def check_response(response):
    """Проверяем ответ API на корректность."""
    if not isinstance(response, dict):
        error_message = 'Неправильный ответ API'
        logging.error(error_message)
        raise TypeError(error_message)
    homeworks = response.get('homeworks')
    if not homeworks:
        error_message = 'Cписок домашних работ пуст!'
        logging.error(error_message)
        raise ValueError(error_message)
    homework = homeworks[0]
    return homework


def parse_status(homework):
    """Получение названия и статуса задания из API."""
    if 'homework_name' not in homework:
        error_message = 'Ключ homework_name отсутствует'
        logging.error(error_message)
        raise KeyError(error_message)
    if 'status' not in homework:
        error_message = 'Ключ status отсутствует'
        logging.error(error_message)
        raise APIWrongStatusException(error_message)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if HOMEWORK_STATUSES[homework_status]:
        verdict = HOMEWORK_STATUSES[homework_status]
    else:
        logging.error('Неизвестный статус работы!!!')
        verdict = 'Неизвестный статус работы!!!'
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов Telegram и Практикума."""
    args = (
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    )
    if not all(args):
        logging.critical('Токен отсутствует!')
        return False
    return True


def main():
    """Основная логика работы бота."""    
    homework = requests.get(ENDPOINT, headers=HEADERS, params=PAYLOAD)
    old_status = homework.json()['homeworks'][0].get('status')
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(TELEGRAM_CHAT_ID, 'Запуск бота.')
    logging.info('Бот запущен.')
    current_timestamp = int(time.time())
    if check_tokens():
        while True:
            try:
                response = get_api_answer(current_timestamp)
                if response:
                    homework = check_response(response)
                    new_status = homework.get('status')
                    if (new_status != old_status):
                        old_status = new_status
                        message = parse_status(homework)
                        send_message(bot, message)
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
            finally:
                time.sleep(RETRY_TIME)
    else:
        raise MissingTokenException("Отсутствуют необходимые токены!")


if __name__ == '__main__':
    main()
