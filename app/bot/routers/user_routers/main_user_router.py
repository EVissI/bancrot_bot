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
from app.bot.midlewares.message_history import track_bot_message
from app.bot.sheldured_task.send_notification import check_user_and_send_notification
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.bot.keyboards.markup_kb import MainKeyboard
from app.db.schemas import TelegramIDModel
from app.config import settings, bot
import re

main_user_router = Router()


class Referal(StatesGroup):
    title = State()
    phone = State()


@main_user_router.message(F.text == MainKeyboard.get_user_kb_texts().get("check_isp"))
async def process_check_isp(message: Message):
    msg = await message.answer("Производится проверка...")
    await check_user_and_send_notification(message.from_user.id)
    await msg.delete()

def is_valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"\+?\d{10,15}", phone.strip()))


def is_valid_fio(fio: str) -> bool:
    return len(fio.strip().split()) >= 2


@main_user_router.message(F.text == MainKeyboard.get_user_kb_texts().get("referal"))
async def process_referal(message: Message, state: FSMContext):
    msg = await message.answer(
        "Введите ваше ФИО и номер телефона, для дальнейшей связи с вами"
    )
    track_bot_message(message.chat.id, msg)
    await state.set_state(Referal.title)


@main_user_router.message(F.text, StateFilter(Referal.title))
async def process_referal_title(message: Message, state: FSMContext):
    if not is_valid_fio(message.text):
        msg = await message.answer(
            "Пожалуйста, введите корректное ФИО (минимум имя и фамилия)"
        )
        track_bot_message(message.chat.id, msg)
        return
    await state.update_data({"title": message.text})
    msg = await message.answer(
        "Введите ФИО и номер телефона человека, которому нужна помощь в банкротстве (через запятую)"
    )
    track_bot_message(message.chat.id, msg)
    await state.set_state(Referal.phone)


@main_user_router.message(F.text, StateFilter(Referal.phone))
async def process_referal(message: Message, state: FSMContext):
    data = await state.get_data()
    referrer_info = data.get("title")
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts) < 2 or not is_valid_fio(parts[0]) or not is_valid_phone(parts[1]):
        msg = await message.answer(
            "Пожалуйста, введите ФИО и номер телефона через запятую, например:\nИванов Иван Иванович, +79991234567"
        )
        track_bot_message(message.chat.id, msg)
        return

    recommended_fio, recommended_phone = parts[0], parts[1]

    async with async_session_maker() as session:
        user = await UserDAO.find_one_or_none(
            session, TelegramIDModel(telegram_id=message.from_user.id)
        )

        if user:
            deal_title = f"{recommended_phone}_{user.user_enter_first_name}_БФЛ_ТГБОТ"
            telegram_link = (
                f"https://t.me/{user.username}"
                if user.username
                else f"tg://user?id={user.telegram_id}"
            )
            comment = (
                f"Рекомендация от: {referrer_info}\n"
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
                f"<b>Рекомендатель:</b> {referrer_info}\n"
                f"<b>Telegram рекомендателя:</b> {telegram_link}"
            )
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

    msg = await message.answer(
        "Спасибо за то что не остались в стороне и решили помочь своему близкому. "
        "Если человек, которому вы решили помочь, оформит у нас банкротство, вы получите 10 000 рублей."
    )
    track_bot_message(message.chat.id, msg)
    await state.clear()


class ReferalComment(StatesGroup):
    waiting_comment = State()


@main_user_router.message(F.text.startswith("/start referal_comment_"))
async def start_referal_comment(message: Message, state: FSMContext):
    deal_id = message.text.split("_")[-1]
    await state.update_data(deal_id=deal_id)
    msg = await message.answer("Введите комментарий для клиента:")
    track_bot_message(message.chat.id, msg)
    await state.set_state(ReferalComment.waiting_comment)


@main_user_router.message(StateFilter(ReferalComment.waiting_comment))
async def process_referal_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    deal_id = data.get("deal_id")
    comment = message.text

    success = await bitrix_add_comment_to_deal(deal_id, comment)
    if success:
        msg = await message.answer("Комментарий отправлен в Bitrix24!")
    else:
        msg = await message.answer("Ошибка при отправке комментария в Bitrix24.")
    track_bot_message(message.chat.id, msg)
    await state.clear()
