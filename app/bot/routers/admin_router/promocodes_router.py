from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from app.bot.keyboards.markup_kb import MainKeyboard, PromocodeKeyboard, BackKeyboard
from app.db.dao import PromocodeDAO
from app.db.database import async_session_maker
from app.db.models import Promocode
from app.db.schemas import PromocodeModel,PromocodeFilterModel
promocode_router = Router()

class CreatePromocodeStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_discount_days = State()
    waiting_for_max_usage = State()

class DeactivatePromocodeStates(StatesGroup):
    waiting_for_code = State()

@promocode_router.message(F.text == MainKeyboard.get_admin_kb_texts('promocods'))
async def process_promo_cmd(message:Message):
    await message.answer(message.text, reply_markup=PromocodeKeyboard.build_promocode_kb())

@promocode_router.message(F.text == PromocodeKeyboard.get_promocode_kb_texts('create_promocode'))
async def start_create_promocode(message: Message, state: FSMContext):
    await state.set_state(CreatePromocodeStates.waiting_for_code)
    await message.answer(
        "Введите код промокода (например: HAPPY2024):",
        reply_markup=BackKeyboard.build_back_kb()
    )


@promocode_router.message(F.text == 'Назад', StateFilter(CreatePromocodeStates))
async def back_create_cmd(message: Message, state: FSMContext):
    await message.answer(message.text,reply_markup=PromocodeKeyboard.build_promocode_kb())
    await state.clear()


@promocode_router.message(StateFilter(CreatePromocodeStates.waiting_for_code))
async def process_promocode_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text)
    await state.set_state(CreatePromocodeStates.waiting_for_discount_days)
    await message.answer("Введите количество дней подписки:")

@promocode_router.message(StateFilter(CreatePromocodeStates.waiting_for_discount_days))
async def process_discount_days(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введите число!")
    
    await state.update_data(discount_days=int(message.text))
    await state.set_state(CreatePromocodeStates.waiting_for_max_usage)
    await message.answer("Введите максимальное количество использований (0 - без ограничений):")

@promocode_router.message(StateFilter(CreatePromocodeStates.waiting_for_max_usage))
async def process_max_usage(message: Message, state: FSMContext):    
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введите число!")
    
    data = await state.get_data()
    code=data['code']
    discount_days=data['discount_days']
    max_usage = int(message.text) if int(message.text) > 0 else None

    async with async_session_maker() as session:
        await PromocodeDAO.add(session,PromocodeModel(
            code=code,
            discount_days=discount_days,
            max_usage=max_usage,
            activate_count=0,
            is_active=True
        ))
    async with async_session_maker() as session:
        promo = await PromocodeDAO.find_one_or_none(session,PromocodeFilterModel(
            code=code,
        ))
        await state.clear()
        await message.answer(
            f"Промокод успешно создан!\n"
            f"Код: {promo.code}\n"
            f"Дней подписки: {promo.discount_days}\n"
            f"Макс. использований: {promo.max_usage or 'без ограничений'}",
            reply_markup=PromocodeKeyboard.build_promocode_kb()
        )

@promocode_router.message(F.text == PromocodeKeyboard.get_promocode_kb_texts('view_promocodes'))
async def view_active_promocodes(message: Message):
    """
    Выводит список активных промокодов, каждый промокод отправляется отдельным сообщением.
    """
    async with async_session_maker() as session:
        active_promocodes = await PromocodeDAO.find_all(session,filters=PromocodeFilterModel(is_active=True))

    if not active_promocodes:
        await message.answer("Нет активных промокодов.", reply_markup=PromocodeKeyboard.build_promocode_kb())
        return

    for promocode in active_promocodes:
        await message.answer(
            f"Код: {promocode.code}\n"
            f"Дней подписки: {promocode.discount_days}\n"
            f"Макс. использований: {promocode.max_usage or 'без ограничений'}\n"
            f"Использовано: {promocode.activate_count}",
            reply_markup=PromocodeKeyboard.build_promocode_kb()
        )

@promocode_router.message(F.text == PromocodeKeyboard.get_promocode_kb_texts('deactivate_promocode'))
async def start_deactivate_promocode(message: Message, state: FSMContext):
    """Начало процесса деактивации промокода"""
    await state.set_state(DeactivatePromocodeStates.waiting_for_code)
    await message.answer(
        "Введите код промокода, который нужно деактивировать",
        reply_markup=BackKeyboard.build_back_kb()
    )

@promocode_router.message(F.text == 'Назад', StateFilter(DeactivatePromocodeStates))
async def back_deactivate_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        message.text,
        reply_markup=PromocodeKeyboard.build_promocode_kb()
    )

@promocode_router.message(StateFilter(DeactivatePromocodeStates.waiting_for_code))
async def process_deactivate_promocode(message: Message, state: FSMContext):
    async with async_session_maker() as session:

        promocode:Promocode = await PromocodeDAO.find_one(
            session, 
            filters=PromocodeFilterModel(code=message.text)
        )
        
        if not promocode:
            await message.answer(
                "Промокод не найден.", 
                reply_markup=BackKeyboard.build_back_kb()
            )
            return
            
        if not promocode.is_active:
            await message.answer(
                "Этот промокод уже деактивирован.", 
                reply_markup=PromocodeKeyboard.build_promocode_kb()
            )
            await state.clear()
            return

        promocode.is_active = False
        async with async_session_maker() as session:
            await PromocodeDAO.update(session,
                                      filters=PromocodeFilterModel(code=message.text),
                                      values=PromocodeFilterModel.model_validate(promocode.to_dict()))
        await message.answer(
            f"Промокод {promocode.code} успешно деактивирован.",
            reply_markup=PromocodeKeyboard.build_promocode_kb()
        )
        await state.clear()

@promocode_router.message(F.text == 'Назад',StateFilter(None))
async def cmd_back(message:Message,state:FSMContext):
    await message.answer(message.text,reply_markup=MainKeyboard.build_main_kb(message.from_user.id))