﻿from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from app.bot.common.msg import messages
from loguru import logger

from app.bot.keyboards.inline_kb import get_subscription_keyboard, get_consent_keyboard
from app.bot.keyboards.markup_kb import get_agreement_keyboard
from app.bot.midlewares.message_history import track_bot_message
from app.db.database import async_session_maker
from app.db.dao import UserDAO
from app.db.schemas import TelegramIDModel, UserModel


registration_router = Router()


class Registration(StatesGroup):
    phone = State()
    fio = State()
    date_of_brth = State()
    region = State()
    old_last_name = State()




@registration_router.callback_query(F.data.startswith("im_ready_to_req"))
async def start_req(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    msg = await callback.message.answer(
        "Перед использованием бота ознакомьтесь с соглашением по кнопке ниже. Если вы согласны, поделитесь номером телефона.",
        reply_markup=get_agreement_keyboard()
    )
    track_bot_message(callback.chat.id, msg)
    await state.set_state(Registration.phone)


@registration_router.message(F.contact, StateFilter(Registration.phone))
async def process_phone(message: Message, state: FSMContext):
    await state.update_data({"phone": message.contact.phone_number})
    msg = await message.answer(
        "Прекрасно, давай знакомиться! Напиши свое ФИО как в паспорте",
        reply_markup=None)
    track_bot_message(message.chat.id, msg)
    await state.set_state(Registration.fio)


@registration_router.message(
    F.text.regexp(r"^\s*\S+(\s+\S+){2}\s*$"), StateFilter(Registration.fio)
)
async def process_fio(message: Message, state: FSMContext):
    await state.update_data({"fio": message.text})
    msg = await message.answer(
        "Приятно познакомиться! Теперь можете написать дату рождения в формате дд.мм.гггг(пример: 29.03.1992)"
    )
    track_bot_message(message.chat.id, msg)
    await state.set_state(Registration.date_of_brth)


@registration_router.message(
    ~F.text.regexp(r"^\s*\S+(\s+\S+){2}\s*$"), StateFilter(Registration.fio)
)
async def error_fio(message: Message):
    msg= await message.answer("Это не похоже на ФИО, попробуйте еще раз")
    track_bot_message(message.chat.id, msg)


@registration_router.message(
    F.text.regexp(r"^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$"),
    StateFilter(Registration.date_of_brth),
)
async def process_dot(message: Message, state: FSMContext):
    await state.update_data({"dot": message.text})
    msg = await message.answer(
        "Теперь пожалуйста, введите регион проживания полностью (например: Удмуртская Республика, Волгоградская область)"
    )
    track_bot_message(message.chat.id, msg)
    await state.set_state(Registration.region)


@registration_router.message(
    ~F.text.regexp(r"^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$"),
    StateFilter(Registration.date_of_brth),
)
async def error_dot(message: Message, state: FSMContext):
    msg = await message.answer("Неверный формат ввода")
    track_bot_message(message.chat.id, msg)


@registration_router.message(F.text, StateFilter(Registration.region))
async def process_region(message: Message, state: FSMContext):
    await state.update_data({"region": message.text})
    msg = await message.answer(
        "Остался последний шаг. Eсли вы меняли фамилию, введите вашу старую фамилию. Если нет, поставьте -"
    )
    track_bot_message(message.chat.id, msg)
    await state.set_state(Registration.old_last_name)


@registration_router.message(F.text, StateFilter(Registration.old_last_name))
async def process_old_last_name(message: Message, state: FSMContext):
    try:
        if message.text == "-":
            await state.update_data({"old_last_name": None})
        else:
            await state.update_data({"old_last_name": message.text})
        state_data = await state.get_data()
        async with async_session_maker() as session:
            telegram_user = await UserDAO.find_one_or_none(
                session, TelegramIDModel(telegram_id=message.from_user.id)
            )
            fio: str = state_data.get("fio")
            last_name, first_name, otchestvo = fio.split(" ")
            user = UserModel(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                phone=state_data.get("phone"),
                user_enter_first_name=first_name,
                user_enter_last_name=last_name,
                user_enter_otchestvo=otchestvo,
                data_of_birth=state_data.get("dot"),
                region=state_data.get("region"),
                old_last_name=state_data.get("old_last_name"),
                end_sub_time=None,
                privacy_accepted=True,
            )
            if telegram_user:
                await UserDAO.update(
                    session,
                    filters=TelegramIDModel(telegram_id=message.from_user.id),
                    values=user,
                )
            else:
                await UserDAO.add(session=session, values=user)
        msg = await message.answer(
            "Отлично,теперь оплатите подписку для дальнейшего пользования ботом",
            reply_markup=get_subscription_keyboard(),
        )
        track_bot_message(message.chat.id, msg)
    except Exception as e:
        logger.error(f"При добавлении юзера произошла ошибка - {str(e)}")
        await message.answer("Что-то пошло не так")
    finally:
        await state.clear()
