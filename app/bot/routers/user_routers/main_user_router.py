from datetime import datetime, timedelta
from aiogram import Router,F
from aiogram.types import CallbackQuery,PreCheckoutQuery,Message
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.sheldured_task.send_notification import check_user_and_send_notification
from app.db.database import async_session_maker
from app.bot.keyboards.markup_kb import MainKeyboard

main_user_router = Router()

class Referal(StatesGroup):
    title = State()
    phone = State()


@main_user_router.message(F.text == MainKeyboard.get_user_kb_texts().get('check_isp'))
async def process_check_isp(message:Message):
    await check_user_and_send_notification(message.from_user.id)

@main_user_router.message(F.text == MainKeyboard.get_user_kb_texts().get('referal'))
async def process_referal(message:Message,state:FSMContext):
    await message.answer('Введите ваше ФИО и номер телефона, для дальнейшей связи с вами')
    await state.set_state(Referal.title)

@main_user_router.message(F.text, StateFilter(Referal.title))
async def process_referal_title(message:Message,state:FSMContext):
    await state.update_data({'title':message.text})
    await message.answer('Введите номер телефона человека, которому нужна помощь в банкротстве')
    await state.set_state(Referal.phone)

@main_user_router.message(F.text, StateFilter(Referal.phone))
async def process_referal(message:Message,state:FSMContext):
    await message.answer('Спасибо за то что не остались в стороне и решили помочь своему близкому. Если человек, которому вы решили помочь, оформит у нас банкротство, вы получите 10 000 рублей.')
    await state.clear()