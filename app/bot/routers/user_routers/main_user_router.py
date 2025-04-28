from datetime import datetime, timedelta
from aiogram import Router,F
from aiogram.types import CallbackQuery,PreCheckoutQuery,Message
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.common.utils import create_bitrix_deal
from app.bot.sheldured_task.send_notification import check_user_and_send_notification
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.bot.keyboards.markup_kb import MainKeyboard
from app.db.schemas import TelegramIDModel

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
    await message.answer('Введите ФИО и номер телефона человека, которому нужна помощь в банкротстве')
    await state.set_state(Referal.phone)

@main_user_router.message(F.text, StateFilter(Referal.phone))
async def process_referal(message:Message,state:FSMContext):
    data = await state.get_data()
    referrer_info = data.get('title')
    phone = message.text

    async with async_session_maker() as session:
        user = await UserDAO.find_one_or_none(
            session, 
            TelegramIDModel(telegram_id=message.from_user.id)
        )
        
        if user:
            deal_title = f"{phone}_{user.user_enter_first_name}_БФЛ_ТГБОТ"
            if user.username:
                telegram_link = f"https://t.me/{user.username}"
            else:
                telegram_link = f"tg://user?id={user.telegram_id}"
            success, result = await create_bitrix_deal(
                title=deal_title,
                comment=f"Рекомендация от: {referrer_info}\nТелеграмм рекомендующего:{telegram_link}",
                category_id='0',  
                stage_id='C0:NEW'
            )
            
            if not success:
                logger.error(f"Failed to create Bitrix deal: {result}")

    await message.answer('Спасибо за то что не остались в стороне и решили помочь своему близкому. Если человек, которому вы решили помочь, оформит у нас банкротство, вы получите 10 000 рублей.')
    await state.clear()