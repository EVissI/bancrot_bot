from datetime import datetime
from aiogram import Router,F
from aiogram.types import Message,CallbackQuery

from loguru import logger

from app.bot.common.utils import create_bitrix_deal
from app.bot.keyboards.inline_kb import BalanceData, check_credit, get_balance_keyboard
from app.bot.keyboards.markup_kb import MainKeyboard
from app.db.dao import UserDAO
from app.db.schemas import TelegramIDModel
from app.db.database import async_session_maker

balance_router = Router()

@balance_router.message(F.text == MainKeyboard.get_user_kb_texts().get('balance'))
async def balance_btn(message: Message):
    """Обработчик кнопки баланса"""
    async with async_session_maker() as session:
        user = await UserDAO.find_one_or_none(
            session,
            TelegramIDModel(telegram_id=message.from_user.id)
        )
        
        if not user:
            await message.answer("Вы не зарегистрированы в системе.")
            return

        await message.answer(
            "Выберите действие:",
            reply_markup=get_balance_keyboard()
        )

@balance_router.callback_query(BalanceData.filter(F.action == 'balance'))
async def process_balance(callback: CallbackQuery):
    """Обработчик нажатия кнопки баланса"""
    async with async_session_maker() as session:
        await callback.answer()
        user = await UserDAO.find_one_or_none(
            session,
            TelegramIDModel(telegram_id=callback.from_user.id)
        )
        
        if not user:
            await callback.answer("Вы не зарегистрированы в системе.")
            return
        await callback.message.delete()
        remaining_time = "Нет активной подписки"
        if user.end_sub_time:
            if user.end_sub_time > datetime.utcnow():
                delta = user.end_sub_time - datetime.utcnow()
                remaining_time = f"Активна еще {delta.days} дней"
            else:
                remaining_time = "Подписка истекла"

        await callback.message.answer(
            f"📊 <b>Ваш баланс</b>\n\n"
            f"Статус подписки: {remaining_time}\n\n"
        )
