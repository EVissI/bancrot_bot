from datetime import datetime
from loguru import logger
import json
from app.bot.common.EFRSB_utils.efrsb_service import find_bankruptcy_by_user
from app.bot.keyboards.inline_kb import stop
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.db.schemas import UserFilterModel,TelegramIDModel
from app.config import bot
from app.bot.common.msg import messages
from pathlib import Path



async def check_db_and_send_notification():
    """
    Проверяет всех пользователей из базы и уведомляет, если найдено банкротство через EFRSB.
    """
    logger.info("Запуск задачи проверки банкротств через EFRSB.")
    async with async_session_maker() as session:
        db_records = await UserDAO.find_all(session, filters=UserFilterModel())
        for db_record in db_records:
            full_name = f"{db_record.user_enter_last_name} {db_record.user_enter_first_name} {db_record.user_enter_otchestvo or ''}".strip()
            birthdate = db_record.data_of_birth
            results = await find_bankruptcy_by_user(full_name, birthdate)
            if results:
                await bot.send_message(
                    db_record.telegram_id,
                    text='‼️ По вашим данным найдено исполнительное производство!\n',reply_markup=stop()
                )
            else:
                await bot.send_message(
                    db_record.telegram_id,
                    text='Исполнительные производства не найдены'
                )

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

        full_name = f"{db_record.user_enter_last_name} {db_record.user_enter_first_name} {db_record.user_enter_otchestvo or ''}".strip()
        birthdate = db_record.data_of_birth

        results = await find_bankruptcy_by_user(full_name, birthdate)

        if results:
            await bot.send_message(
                db_record.telegram_id,
                text='‼️ По вашим данным найдено исполнительное производство!\n',reply_markup=stop()
            )
        else:
            await bot.send_message(
                db_record.telegram_id,
                text='Исполнительные производства не найдены'
            )