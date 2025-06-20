from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    PreCheckoutQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.common.utils import create_bitrix_deal, bitrix_add_comment_to_deal
from app.bot.keyboards.inline_kb import referal_keyboard, referal_keyboard_v2
from app.bot.midlewares.message_history import track_bot_message
from app.bot.sheldured_task.send_notification import check_user_and_send_notification
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.bot.keyboards.markup_kb import MainKeyboard
from app.db.schemas import TelegramIDModel, UserFilterModel
from app.config import settings, bot
from app.bot.common.msg import messages
import re

main_user_router = Router()


class Referal(StatesGroup):
    fio = State()
    phone = State()


@main_user_router.message(F.text == MainKeyboard.get_user_kb_texts().get("check_isp"))
async def process_check_isp(message: Message):
    async with async_session_maker() as session:
        user = await UserDAO.find_one_or_none(
            session, TelegramIDModel(telegram_id=message.from_user.id)
        )
        if not user.can_use_fccp:
            msg = await message.answer(messages.get('second_use_fccp_module'),reply_markup=referal_keyboard())
            track_bot_message(message.from_user.id, msg)
            return
        msg = await message.answer("Производится проверка...")
        await check_user_and_send_notification(message.from_user.id)
        await msg.delete()
        async with async_session_maker() as session:
            user.can_use_fccp = False
            await UserDAO.update(session, TelegramIDModel(telegram_id=message.from_user.id),
                                    UserFilterModel.model_validate(user.to_dict()))

def is_valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"\+?\d{10,15}", phone.strip()))


def is_valid_fio(fio: str) -> bool:
    return len(fio.strip().split()) >= 2


@main_user_router.message((F.text == MainKeyboard.get_user_kb_texts().get("referal")))
async def process_referal(message: Message, state: FSMContext):
    msg = await message.answer(
        "Введите ФИО человека которому вы хотите помочь"
    )
    track_bot_message(message.chat.id, msg)
    await state.set_state(Referal.fio)

@main_user_router.callback_query(F.data == "referal")
async def process_referal_query(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await query.message.delete()
    msg = await query.message.answer(
        "Введите ФИО человека которому вы хотите помочь"
    )
    track_bot_message(query.message.chat.id, msg)
    await state.set_state(Referal.fio)

@main_user_router.message(F.text, StateFilter(Referal.fio))
async def process_referal_title(message: Message, state: FSMContext):
    if not is_valid_fio(message.text):
        msg = await message.answer(
            "Пожалуйста, введите корректное ФИО (минимум имя и фамилия)"
        )
        track_bot_message(message.chat.id, msg)
        return
    await state.update_data({"fio": message.text})
    msg = await message.answer(
        "Введите Его номер телефона в формате: +79991234567 или 89991234567"
    )
    track_bot_message(message.chat.id, msg)
    await state.set_state(Referal.phone)


@main_user_router.message(F.text, StateFilter(Referal.phone))
async def process_referal(message: Message, state: FSMContext):
    data = await state.get_data()
    if not is_valid_phone(message.text):
        msg = await message.answer(
            "Пожалуйста, введите корректный номер телефона в формате: +79991234567 или 89991234567"
        )
        track_bot_message(message.chat.id, msg)
        return
    recommended_fio = data.get("fio") 
    recommended_phone = message.text.strip()

    async with async_session_maker() as session:
        user = await UserDAO.find_one_or_none(
            session, TelegramIDModel(telegram_id=message.from_user.id)
        )

        if user:
            referrer_fio = (
                f"{user.user_enter_last_name} {user.user_enter_first_name} "
                f"{user.user_enter_otchestvo}" if user.user_enter_otchestvo else
                f"{user.user_enter_last_name} {user.user_enter_first_name}"
            )
            deal_title = f"{recommended_phone}_{user.user_enter_first_name}_БФЛ_ТГБОТ"
            telegram_link = (
                f"https://t.me/{user.username}"
                if user.username
                else f"tg://user?id={user.telegram_id}"
            )
            comment = (
                f"Рекомендация от: {referrer_fio}\n"
                f"Телеграмм рекомендующего: {telegram_link}\n"
                f"Рекомендуемый: {recommended_fio}, {recommended_phone}"
            )
            success, result = await create_bitrix_deal(
                title=deal_title, comment=comment, category_id="0", stage_id="C0:NEW"
            )
            if not success:
                logger.error(f"Failed to create Bitrix deal: {result}")

            telegram_link = (
                f"https://t.me/{user.username}"
                if user.username
                else f"tg://user?id={user.telegram_id}"
            )
            notify_text = (
                "🆕 <b>Новая заявка: Рекомендация друга (БФЛ)</b>\n"
                f"<b>Рекомендуемый:</b> {recommended_fio}\n"
                f"<b>Телефон:</b> {recommended_phone}\n"
                f"<b>Рекомендатель:</b> {referrer_fio}\n"
                f"<b>Telegram рекомендателя:</b> {telegram_link}"
            )
            logger.info(result)
            if result:
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Ответить клиенту",
                                url=f"https://t.me/{settings.BOT_USERNAME}?start=referal_comment_{result}",
                            )
                        ]
                    ]
                )
            else:
                kb = None

            await bot.send_message(
                settings.WORK_CHAT_ID, notify_text, parse_mode="HTML", reply_markup=kb
            )

    text = f"""🌟<b>✨ Благодарим за вашу рекомендацию!</b>
Мы свяжемся с <b>{recommended_fio}</b> по номеру <b>{recommended_phone}</b> в ближайшее время.

🔥 <b>Но почему бы не пойти дальше?</b>
Чем больше друзей вы приведете, тем выше будет ваша персональная премия:

• 5 друзей = <b>75 000₽</b>
• 10 друзей = <b>200 000₽</b>

👉 <b>Продолжайте рекомендовать и экономьте:</b>"""
    msg = await message.answer(
        text, reply_markup=referal_keyboard_v2()
    )
    track_bot_message(message.chat.id, msg)
    await state.clear()




