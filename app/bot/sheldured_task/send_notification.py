import time
from loguru import logger
import json

import requests
from app.bot.keyboards.inline_kb import referal_keyboard, stop
from app.bot.midlewares.message_history import track_bot_message
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.db.schemas import UserFilterModel,TelegramIDModel
from app.config import bot
from app.bot.common.msg import messages
from pathlib import Path


current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent.parent
tasks_path = 'retry_tasks.json'
db_path = project_root / 'fccp_bot' / 'bot1' / 'all_data.json'
api_path = project_root / 'fccp_bot' / 'bot1' / 'api.txt'
url = 'https://service.api-assist.com/parser/info_api/'


def scan_sum_to_pay(data):
    all_payments = 0
    for person in data:
        all_payments += int(person['payment_available'])
    
    return all_payments


async def check_user(db_record):
    with open(api_path, 'r', encoding='utf-8') as file:
        api_key = file.read()

    params = {
        'type': 'TYPE_SEARCH_FIZ',
        'regionID': '-1',
        'lastName': db_record.user_enter_last_name,
        'firstName': db_record.user_enter_first_name,
        'patronymic': db_record.user_enter_otchestvo,
        'dob': db_record.data_of_birth,
        'key': api_key
    }
    wait = 60
    for _ in range(3):
        try:
            resp = requests.get(url, params, timeout=10)
            logger.info(f'{resp.status_code}, {len(resp.content)}, {resp.content[:100]}')
            js_data = resp.json()
            if js_data.get('done'): break
            if js_data['error'] == 'fssprus.ru is temporarily unavailable, please try again later':
                wait *= 2
                time.sleep(wait)
            elif js_data['error'] == 'Day limit of requests exceeded':
                logger.info('Дневной лимит запроса исчерпан!\n!Загрузка поставлено в паузу на 24 часа!')
                time.sleep(86400)
            else:
                wait *= 5
                time.sleep(wait)
                
        except Exception as e:
            logger.error(f'Request error: {e}')
            js_data = {'error': str(e)}
    else:
        raise Exception(js_data['error'])

    for person in js_data['result']:
        sum_to_pay = int(person['payment_available'])
        if sum_to_pay > 0:
            msg = await bot.send_message(db_record.telegram_id,text='Обнаружено исполнительное производство! Нажмите кнопку',
                                reply_markup=stop(f"{person['process_title']} от {person.get('process_date')}" if 'process_title' in person else ''))
            track_bot_message(db_record.telegram_id, msg, ignore=True)
            msg = await bot.send_message(db_record.telegram_id,text=messages.get('referal'))
            track_bot_message(db_record.telegram_id, msg, ignore=True)
            break
    
    else:
        logger.info("Запись не найдена.")
        msg = await bot.send_message(db_record.telegram_id,text='Исполнительные производства не найдены')
        track_bot_message(db_record.telegram_id, msg, ignore=True)
        msg = await bot.send_message(db_record.telegram_id,text=messages.get('referal'),reply_markup=referal_keyboard())
        track_bot_message(db_record.telegram_id, msg, ignore=True)


async def retry_tasks_launch(last=False):
    logger.info("Запуск запланированные задачи.")
    
    try:
        with open(tasks_path, 'r', encoding='utf-8') as file:
            retry_tasks = json.load(file)
    except FileNotFoundError:
        retry_tasks = []

    new_retry_tasks = []
    async with async_session_maker() as session:
        # Получаем все записи из базы данных
        cnt = 0
        full = len(retry_tasks)
        for telegram_id in retry_tasks:
            db_record = await UserDAO.find_one_or_none(session,filters=TelegramIDModel(telegram_id=telegram_id))
            if not db_record:
                logger.info(f"Пользователь с telegram_id {telegram_id} не найден в базе данных.")
                continue
            
            cnt += 1
            logger.info(f'Загрузка...\n{round((100*cnt)/full, 2)}%')
            try:
                await check_user(db_record)
            except Exception as e:
                logger.error(f'Error: {e}')
                if last:
                    msg = await bot.send_message(
                                        telegram_id,
                                        text='База ФССП временно недоступна. Мы предоставим информацию позже.'
                                    )
                    track_bot_message(telegram_id, msg)
                else:
                    new_retry_tasks.append(db_record.telegram_id)
    
    with open(tasks_path, 'w', encoding='utf-8') as file:
        json.dump(new_retry_tasks, file, ensure_ascii=False)


async def second_retry_tasks_launch():
    await retry_tasks_launch()


async def last_retry_tasks_launch():
    await retry_tasks_launch(last=True)



async def check_db_and_send_notification():
    """

    Проверка из базы ФССП.
    """
    logger.info("Запуск задачи по проверке из базы ФССП.")
    
    try:
        with open(tasks_path, 'r', encoding='utf-8') as file:
            retry_tasks = json.load(file)
    except FileNotFoundError:
        retry_tasks = []


    async with async_session_maker() as session:
        db_records = await UserDAO.find_all(session, filters=UserFilterModel())

        db_records = list(db_records)
        cnt = 0
        full = len(db_records)
        for db_record in db_records:
            cnt += 1
            logger.info(f'Загрузка...\n{round((100*cnt)/full, 2)}%')
            try:
                await check_user(db_record)
            except Exception as e:
                logger.error(f'Error: {e}')
                retry_tasks.append(db_record.telegram_id)

    with open(tasks_path, 'w', encoding='utf-8') as file:
        json.dump(retry_tasks, file, ensure_ascii=False)


async def check_user_and_send_notification(telegram_id: int):
    """
    Проверяет пользователя из базы и уведомляет, если найдено банкротство через EFRSB.
    """
    logger.info(f"Запуск задачи проверки для пользователя с telegram_id: {telegram_id}")

    async with async_session_maker() as session:
        db_record = await UserDAO.find_one_or_none(session, filters=TelegramIDModel(telegram_id=telegram_id))

        if not db_record:
            logger.info(f"Пользователь с telegram_id {telegram_id} не найден в базе данных.")
            return

        
        try:
            await check_user(db_record)
        except Exception as e:
            logger.error(f'Error: {e}')
            await bot.send_message(
                                db_record.telegram_id,
                                text='База ФССП временно недоступна. Мы предоставим информацию позже.'
                            )
    