from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from app.bot.common.msg import messages
from loguru import logger

from app.bot.keyboards.inline_kb import (
    ConfirmInRegistrationCallbackData,
    LastNameChangeCallback,
    RegFullConfirmCallbackData,
    build_has_last_name_changed,
    build_req_confirm_kb,
    build_req_full_confirm_kb,
    get_subscription_keyboard,
    get_consent_keyboard,
)
from app.bot.keyboards.markup_kb import (
    BackKeyboard,
    MainKeyboard,
    get_agreement_keyboard,
)
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

@registration_router.message(
    F.text == BackKeyboard.get_button_text(), StateFilter(Registration)
)
async def cmd_back(message: Message, state: FSMContext):
    current_state = await state.get_state()
    match current_state:
        case Registration.fio.state:
            # Возврат к вводу телефона
            await message.answer(
                "Перед использованием бота ознакомьтесь с соглашением по кнопке ниже. Если вы согласны, поделитесь номером телефона.",
                reply_markup=get_agreement_keyboard(),
            )
            await state.set_state(Registration.phone)

        case Registration.date_of_brth.state:
            await message.answer(
                "Напиши свое ФИО как в паспорте (например: Иванов Иван Иванович)\n\n Это нужно для поиска в базе ФССП",
                reply_markup=BackKeyboard.build_back_kb(),
            )
            await state.set_state(Registration.fio)

        case Registration.region.state:
            # Возврат к вводу даты рождения
            await message.answer(
                "Напишите дату рождения в формате дд.мм.гггг(например: 29.03.1992)\n\n Это необходимо для точной идентификации и исключения однофамильцев",
                reply_markup=BackKeyboard.build_back_kb(),
            )
            await state.set_state(Registration.date_of_brth)

        case Registration.old_last_name.state:
            # Возврат к вводу региона
            await message.answer(
                "Укажите регион для сужения области поиска и повышения точности (например: Удмуртская Республика, Волгоградская область)",
                reply_markup=BackKeyboard.build_back_kb(),
            )
            await state.set_state(Registration.region)

        case Registration.phone.state:
            # Возврат в главное меню
            await message.answer(
                "Регистрация отменена",
                reply_markup=MainKeyboard.build_main_kb(message.from_user.id),
            )
            await state.clear()


@registration_router.callback_query(F.data.startswith("im_ready_to_req"))
async def start_req(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "Перед использованием бота ознакомьтесь с соглашением по кнопке ниже. Если вы согласны, поделитесь номером телефона.",
        reply_markup=get_agreement_keyboard(),
    )
    await state.set_state(Registration.phone)


@registration_router.message(F.contact, StateFilter(Registration.phone))
async def process_phone(message: Message, state: FSMContext):
    await state.update_data({"phone": message.contact.phone_number})
    await message.answer(
        "Прекрасно, давай знакомиться! Напиши свое ФИО как в паспорте (например: Иванов Иван Иванович)\n\n Это нужно для поиска в базе ФССП",
        reply_markup=BackKeyboard.build_back_kb(),
    )
    await state.set_state(Registration.fio)




@registration_router.message(
    F.text.regexp(r"^\s*\S+(\s+\S+){2}\s*$"), StateFilter(Registration.fio)
)
async def process_fio(message: Message, state: FSMContext):
    await state.update_data({"fio": message.text})
    await message.answer(
        "Напишите дату рождения в формате дд.мм.гггг(например: 29.03.1992)\n\n Это необходимо для точной идентификации и исключения однофамильцев"
    )
    await state.set_state(Registration.date_of_brth)


@registration_router.message(
    ~F.text.regexp(r"^\s*\S+(\s+\S+){2}\s*$"), StateFilter(Registration.fio)
)
async def error_fio(message: Message):
    await message.answer(
        "Это не похоже на ФИО (например: Иванов Иван Иванович), попробуйте снова"
    )


@registration_router.message(
    F.text.regexp(r"^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$"),
    StateFilter(Registration.date_of_brth),
)
async def process_dot(message: Message, state: FSMContext):
    await state.update_data({"dot": message.text})
    data = await state.get_data()
    await message.answer(
        f"ФИО: {data.get('fio')}\nДата рождения: {data.get('dot')}",
        reply_markup=build_req_confirm_kb(),
    )


@registration_router.callback_query(
    ConfirmInRegistrationCallbackData.filter(F.action == "confirm")
)
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "Укажите регион для сужения области поиска и повышения точности (например: Удмуртская Республика, Волгоградская область)\n\n "
    )
    await state.set_state(Registration.region)


@registration_router.callback_query(
    ConfirmInRegistrationCallbackData.filter(F.action == "change")
)
async def process_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "Напиши свое ФИО как в паспорте (например: Иванов Иван Иванович)\n\n Это нужно для поиска в базе ФССП",
        reply_markup=BackKeyboard.build_back_kb(),
    )
    await state.set_state(Registration.fio)


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
        "Вы меняли фамилию (например, после замужества)?",
        reply_markup=build_has_last_name_changed(),
    )


@registration_router.callback_query(LastNameChangeCallback.filter(F.flag == True))
async def process_change_last_name_yes(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Введите вашу старую фамилию")
    await state.set_state(Registration.old_last_name)


@registration_router.message(F.text, StateFilter(Registration.old_last_name))
async def process_change_last_name_text(message: Message, state: FSMContext):
    await state.update_data({"old_last_name": message.text})
    state_data = await state.get_data()
    formatted_text = (
        "<b>Проверьте введенные данные:</b>\n\n"
        f"📱 Телефон: <code>{state_data.get('phone')}</code>\n"
        f"👤 ФИО: <code>{state_data.get('fio')}</code>\n"
        f"📅 Дата рождения: <code>{state_data.get('dot')}</code>\n"
        f"📍 Регион: <code>{state_data.get('region')}</code>\n"
    )
    
    if state_data.get('old_last_name'):
        formatted_text += f"📝 Предыдущая фамилия: <code>{state_data.get('old_last_name')}</code>\n"
    
    await message.answer(formatted_text, 
                                  reply_markup=build_req_full_confirm_kb(), 
                                  parse_mode="HTML")
    

@registration_router.callback_query(LastNameChangeCallback.filter(F.flag == False))
async def process_change_last_name_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    state_data = await state.get_data()
    formatted_text = (
        "<b>Проверьте введенные данные:</b>\n\n"
        f"📱 Телефон: <code>{state_data.get('phone')}</code>\n"
        f"👤 ФИО: <code>{state_data.get('fio')}</code>\n"
        f"📅 Дата рождения: <code>{state_data.get('dot')}</code>\n"
        f"📍 Регион: <code>{state_data.get('region')}</code>\n"
    )
    
    if state_data.get('old_last_name'):
        formatted_text += f"📝 Предыдущая фамилия: <code>{state_data.get('old_last_name')}</code>\n"
    
    await callback.message.answer(formatted_text, 
                                  reply_markup=build_req_full_confirm_kb(), 
                                  parse_mode="HTML")

@registration_router.callback_query(
    RegFullConfirmCallbackData.filter(F.action == "change")
)
async def process_old_last_name_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "Напиши свое ФИО как в паспорте (например: Иванов Иван Иванович)\n\n Это нужно для поиска в базе ФССП",
        reply_markup=BackKeyboard.build_back_kb(),
    )
    await state.set_state(Registration.fio)


@registration_router.callback_query(
    RegFullConfirmCallbackData.filter(F.action == "confirm")
)
async def process_old_last_name(callback: CallbackQuery, state: FSMContext):
    try:
        state_data = await state.get_data()
        async with async_session_maker() as session:
            telegram_user = await UserDAO.find_one_or_none(
                session, TelegramIDModel(telegram_id=callback.from_user.id)
            )
            fio: str = state_data.get("fio")
            last_name, first_name, otchestvo = fio.split(" ")
            user = UserModel(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
                phone=state_data.get("phone"),
                user_enter_first_name=first_name,
                user_enter_last_name=last_name,
                user_enter_otchestvo=otchestvo,
                data_of_birth=state_data.get("dot"),
                region=state_data.get("region"),
                old_last_name=state_data.get("old_last_name"),
                privacy_accepted=True,
            )
            if telegram_user:
                await UserDAO.update(
                    session,
                    filters=TelegramIDModel(telegram_id=callback.from_user.id),
                    values=user,
                )
            if not telegram_user:
                await UserDAO.add(session=session, values=user)
        await callback.message.answer(
            'Спасибо, теперь вам доступны функции "Проверить ИП" и "Партнерская программа"',
            reply_markup=MainKeyboard.build_main_kb(callback.from_user.id),
        )
    except Exception as e:
        logger.error(f"При добавлении юзера произошла ошибка - {str(e)}")
        await callback.message.answer(
            "Ошибка на стороне сервера, попробуйте снова позже"
        )
    finally:
        await state.clear()
