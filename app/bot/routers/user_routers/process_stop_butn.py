from aiogram import Router,F
from aiogram.types import CallbackQuery
from loguru import logger
import requests

from app.config import settings
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.db.schemas import TelegramIDModel
stop_router = Router()

@stop_router.callback_query(F.data.startswith("stop"))
async def process_stop(query:CallbackQuery):
    try:
        async with async_session_maker() as session:
            user_from_db = await UserDAO.find_one_or_none(session,TelegramIDModel(telegram_id=query.from_user.id))
        user = {
        'telegram_id': user_from_db.telegram_id,
        'username': user_from_db.username,
        'first_name': user_from_db.user_enter_first_name,
        'last_name': user_from_db.user_enter_last_name,
        'user_enter_fio': f'{user_from_db.user_enter_last_name} {user_from_db.user_enter_first_name} {user_from_db.user_enter_otchestvo}',
        'data_of_birth': user_from_db.data_of_birth,
        'region': user_from_db.region,
        'old_last_name': user_from_db.old_last_name
        }
        if user_from_db.username:
            telegram_link = f"https://t.me/{user_from_db.username}"
        else:
            telegram_link = f"tg://user?id={user_from_db.telegram_id}"
        old_last_name = f"Предыдущее фамилия: {user['old_last_name']}" if user.get('old_last_name') else ''
        comment_msg = f'Ссылка на тг: {telegram_link}' + old_last_name
        lead_data = {
                'fields': {
                    'TITLE': f"Лид от пользователя {user['first_name']} {user['last_name']}",
                    'NAME': user['first_name'],
                    'LAST_NAME': user['last_name'],
                    'SECOND_NAME': user.get('user_enter_fio', '').split()[1] if user.get('user_enter_fio') else '',
                    'BIRTHDATE': user['data_of_birth'],
                    'ADDRESS_CITY': user['region'],
                    'COMMENTS': comment_msg,
                    'SOURCE_ID': 'WEB',  
                    'STATUS_ID': 'NEW',
                    'OPENED': 'Y',
                    'ASSIGNED_BY_ID': 1, 
                    'PHONE': [
                        {
                            'VALUE': '1234567890',
                            'VALUE_TYPE': 'WORK'
                        }
                    ],
                    'EMAIL': [
                        {
                            'VALUE': 'user@example.com',
                            'VALUE_TYPE': 'WORK'
                        }
                    ]
                }
            }
        response = requests.post(f"{settings.BITRIKS_WEBHOOK_URL}crm.lead.list",json=lead_data)
        result = response.json()

        if 'result' in result:
            logger.info(f"Лид успешно создан с ID: {result['result']}")
            await query.message.delete()
            await query.message.answer('Отлично, скоро с вами свяжется наш менеджер')
        else:
            logger.info(f"Ошибка при создании лида: {result['error_description']}")
            await query.message.delete()
            await query.message.answer('Произошла ошибка на сервере, попробуйте позже')

    except Exception as e:
        logger.error(f'При отправке лида от юзера {query.from_user.id} произошла ошибка - {str(e)}')
        await query.answer('Что-то пошло не так')