from aiogram import Router,F
from aiogram.types import CallbackQuery,Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup

from loguru import logger

from app.bot.keyboards.inline_kb import get_subscription_keyboard
from app.db.database import async_session_maker
from app.db.dao import UserDAO
from app.db.schemas import UserModel


registration_router = Router()


class Registration(StatesGroup):
    fio = State()
    date_of_brth = State()
    region = State()
    old_last_name = State()


@registration_router.callback_query(F.data.startswith("im_ready_to_req"))
async def start_req(callback: CallbackQuery,state:FSMContext):
    await callback.message.delete()
    await callback.message.answer('Прекрасно, давай знакомиться! Напиши свое ФИО как в паспорте')
    await state.set_state(Registration.fio)

@registration_router.message(F.text.regexp(r"^\s*\S+(\s+\S+){2}\s*$"),StateFilter(Registration.fio))
async def process_fio(message:Message,state:FSMContext):
    await state.update_data({'fio':message.text})
    await message.answer('Приятно познакомиться! Теперь можете написать дату рождения в формате год-месяц-день')
    await state.set_state(Registration.date_of_brth)

@registration_router.message(~F.text.regexp(r"^\s*\S+(\s+\S+){2}\s*$"),StateFilter(Registration.fio))
async def error_fio(message:Message):
    await message.answer('Это не похоже на ФИО, попробуйте еще раз')

@registration_router.message(F.text.regexp(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"),StateFilter(Registration.date_of_brth))
async def process_dot(message:Message,state:FSMContext):
    await state.update_data({'dot':message.text})
    await message.answer('Теперь пожалуйста, введите город в котором вы проживаете')
    await state.set_state(Registration.region)

@registration_router.message(~F.text.regexp(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"),StateFilter(Registration.date_of_brth))
async def error_dot(message:Message,state:FSMContext):
    await message.answer('Неверный формат ввода(подсказка: тире важны)')

@registration_router.message(F.text, StateFilter(Registration.region))
async def process_region(message:Message,state:FSMContext):
    await state.update_data({'region':message.text})
    await message.answer('Остался последний шаг. Eсли вы меняли фамилию, введите вашу старую фамилию. Если нет, поставьте -')
    await state.set_state(Registration.old_last_name)

@registration_router.message(F.text, StateFilter(Registration.old_last_name))
async def process_old_last_name(message:Message,state:FSMContext):
    try:
        if message.text == '-':
            await state.update_data({'old_last_name':None})
        else:
            await state.update_data({'old_last_name':message.text})
        state_data = await state.get_data()
        async with async_session_maker() as session:
            fio:str = state_data.get('fio')
            last_name, first_name, otchestvo = fio.split(' ')
            user = UserModel(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                user_enter_first_name=first_name,
                user_enter_last_name=last_name,
                user_enter_otchestvo=otchestvo,
                data_of_birth=state_data.get('dot'),
                region=state_data.get('region'),
                old_last_name=state_data.get('old_last_name'),
                end_sub_time=None
            )
            await UserDAO.add(session=session,values=user)
        await message.answer('Отлично,теперь оплатите подписку для дальнейшего пользования ботом',reply_markup=get_subscription_keyboard())
    except Exception as e:
        logger.error(f'При добавлении юзера произошла ошибка - {str(e)}')
        await message.answer('Что-то пошло не так')
    finally:
        await state.clear()