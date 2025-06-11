from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from app.bot.common.msg import messages as  msg
from loguru import logger

from app.bot.keyboards.inline_kb import get_subscription_keyboard, get_consent_keyboard
from app.db.database import async_session_maker
from app.db.dao import UserDAO
from app.db.schemas import TelegramIDModel, UserModel


registration_router = Router()


class Registration(StatesGroup):
    consent = State()  # New state for privacy consent
    fio = State()
    date_of_brth = State()
    region = State()
    old_last_name = State()




@registration_router.callback_query(F.data.startswith("im_ready_to_req"))
async def start_req(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        msg.get("privacy"), reply_markup=get_consent_keyboard(), parse_mode="Markdown"
    )
    await state.set_state(Registration.consent)


@registration_router.callback_query(
    F.data == "decline_privacy", StateFilter(Registration.consent)
)
async def decline_privacy(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "❌ Без согласия на обработку персональных данных использование бота невозможно. "
        "Если передумаете, начните регистрацию заново командой /start"
    )
    await state.clear()


@registration_router.callback_query(
    F.data == "accept_privacy", StateFilter(Registration.consent)
)
async def accept_privacy(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "Прекрасно, давай знакомиться! Напиши свое ФИО как в паспорте"
    )
    await state.set_state(Registration.fio)


@registration_router.message(
    F.text.regexp(r"^\s*\S+(\s+\S+){2}\s*$"), StateFilter(Registration.fio)
)
async def process_fio(message: Message, state: FSMContext):
    await state.update_data({"fio": message.text})
    await message.answer(
        "Приятно познакомиться! Теперь можете написать дату рождения в формате дд.мм.гггг(пример: 29.03.1992)"
    )
    await state.set_state(Registration.date_of_brth)


@registration_router.message(
    ~F.text.regexp(r"^\s*\S+(\s+\S+){2}\s*$"), StateFilter(Registration.fio)
)
async def error_fio(message: Message):
    await message.answer("Это не похоже на ФИО, попробуйте еще раз")


@registration_router.message(
    F.text.regexp(r"^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$"),
    StateFilter(Registration.date_of_brth),
)
async def process_dot(message: Message, state: FSMContext):
    await state.update_data({"dot": message.text})
    await message.answer(
        "Теперь пожалуйста, введите регион проживания полностью (например: Удмуртская Республика, Волгоградская область)"
    )
    await state.set_state(Registration.region)


@registration_router.message(
    ~F.text.regexp(r"^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$"),
    StateFilter(Registration.date_of_brth),
)
async def error_dot(message: Message, state: FSMContext):
    await message.answer("Неверный формат ввода")


@registration_router.message(F.text, StateFilter(Registration.region))
async def process_region(message: Message, state: FSMContext):
    await state.update_data({"region": message.text})
    await message.answer(
        "Остался последний шаг. Eсли вы меняли фамилию, введите вашу старую фамилию. Если нет, поставьте -"
    )
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
        await message.answer(
            "Отлично,теперь оплатите подписку для дальнейшего пользования ботом",
            reply_markup=get_subscription_keyboard(),
        )
    except Exception as e:
        logger.error(f"При добавлении юзера произошла ошибка - {str(e)}")
        await message.answer("Что-то пошло не так")
    finally:
        await state.clear()
