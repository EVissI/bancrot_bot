from aiogram import Router,F
from aiogram.types import Message,CallbackQuery

from loguru import logger

from app.bot.common.utils import create_bitrix_deal
from app.bot.keyboards.inline_kb import check_credit
from app.bot.keyboards.markup_kb import MainKeyboard
from app.db.dao import UserDAO
from app.db.schemas import TelegramIDModel
from app.db.database import async_session_maker

credits_router = Router()

@credits_router.message(F.text == MainKeyboard.get_user_kb_texts().get('check_credit'))
async def process_check_credit(message:Message):
    await message.answer('Кредитная история',reply_markup=check_credit())

@credits_router.callback_query(F.data == 'dispute_credit')
async def process_dispute_credit(callback:CallbackQuery):
    async with async_session_maker() as session:
        user_from_db = await UserDAO.find_one_or_none(session,TelegramIDModel(telegram_id=callback.from_user.id))
    if user_from_db.username:
        telegram_link = f"https://t.me/{user_from_db.username}"
    else:
        telegram_link = f"tg://user?id={user_from_db.telegram_id}"
    old_last_name = f"Предыдущее фамилия: {user_from_db.old_last_name}" if user_from_db.old_last_name else ''
    region = f"Регион: {user_from_db.region}"
    date_of_birth = f"Дата рождения: {user_from_db.data_of_birth}"
    comment_msg = f'Ссылка на тг: {telegram_link}\n{old_last_name}\n{region}\n{date_of_birth}' 
    if user_from_db.user_enter_otchestvo:
        fio = f"{user_from_db.user_enter_last_name} {user_from_db.user_enter_first_name} {user_from_db.user_enter_otchestvo}"
    else:
        fio = f"{user_from_db.user_enter_last_name} {user_from_db.user_enter_first_name}"
    success, result = await create_bitrix_deal(title=f'{fio}_КРЕДИТНАЯ_ИСТОРИЯ_ТГБОТ',comment=comment_msg,category_id='7',stage_id='PREPARATION')
    if success:
        await callback.message.delete()
        await callback.message.answer('Отлично, скоро с вами свяжется наш менеджер')
    else:
        logger.error(f"Ошибка при создании сделки: {result}")
        await callback.message.delete()
        await callback.message.answer('Произошла ошибка на сервере, попробуйте позже')

