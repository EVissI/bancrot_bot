from datetime import datetime, timedelta
from aiogram import Router,F
from aiogram.types import CallbackQuery
from loguru import logger
import requests

from app.bot.common.utils import create_bitrix_deal
from app.bot.keyboards.inline_kb import StopBancrData, referal_keyboard
from app.bot.midlewares.message_history import track_bot_message
from app.config import settings
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.db.schemas import TelegramIDModel, UserFilterModel
from app.bot.common.msg import messages
stop_router = Router()

@stop_router.callback_query(StopBancrData.filter())
async def process_stop(query: CallbackQuery, callback_data:StopBancrData):
    try:
        async with async_session_maker() as session:
            user_from_db = await UserDAO.find_one_or_none(session,TelegramIDModel(telegram_id=query.from_user.id))

        if not user_from_db.can_use_fccp:
            msg = await query.message.answer(messages.get('second_use_fccp_module'),reply_markup=referal_keyboard())
            track_bot_message(query.from_user.id, msg)
            return
        if user_from_db.username:
            telegram_link = f"https://t.me/{user_from_db.username}"
        else:
            telegram_link = f"tg://user?id={user_from_db.telegram_id}"
        old_last_name = f"Предыдущее фамилия: {user_from_db.old_last_name}" if user_from_db.old_last_name else ''
        IE = f"ИНН: {callback_data.IE}"
        region = f"Регион: {user_from_db.region}"
        date_of_birth = f"Дата рождения: {user_from_db.data_of_birth}"
        comment_msg = f'{IE}\nСсылка на тг: {telegram_link}\n{old_last_name}\n{region}\n{date_of_birth}' 

        if user_from_db.user_enter_otchestvo:
            fio = f"{user_from_db.user_enter_last_name} {user_from_db.user_enter_first_name} {user_from_db.user_enter_otchestvo}"
        else:
            fio = f"{user_from_db.user_enter_last_name} {user_from_db.user_enter_first_name}"

        success, result = await create_bitrix_deal(title=f'{fio}_ТГБОТ',comment=comment_msg,category_id='7',stage_id='C7:UC_CYWJJ2')
        if success:
            await query.message.delete()
            msg = await query.message.answer('Отлично, скоро с вами свяжется наш менеджер')
            track_bot_message(query.from_user.id, msg)
            async with async_session_maker() as session:
                user_from_db.can_use_fccp = False
                await UserDAO.update(session, TelegramIDModel(telegram_id=query.from_user.id),
                                      UserFilterModel.model_validate(user_from_db.to_dict()))
        else:
            logger.error(f"Ошибка при создании сделки: {result}")
            await query.message.delete()
            msg = await query.message.answer('Произошла ошибка на сервере, попробуйте позже')
            track_bot_message(query.from_user.id, msg)

    except Exception as e:
        logger.error(f'При отправке лида от юзера {query.from_user.id} произошла ошибка - {str(e)}')
        await query.answer('Что-то пошло не так')