from app.bot.common.msg import messages
from aiogram import Router,F
from aiogram.filters import CommandStart,StateFilter
from aiogram.types import Message,CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.common.utils import bitrix_add_comment_to_deal
from app.bot.keyboards.inline_kb import get_subscription_on_chanel_keyboard, im_ready,get_subscription_keyboard
from app.bot.keyboards.markup_kb import MainKeyboard, get_agreement_keyboard
from app.bot.midlewares.admin_middleware import CheckAdmin
from app.bot.midlewares.check_sub import CheckSub
from app.bot.midlewares.check_sub_to_bot import CheckPaidSubscription
from app.bot.midlewares.message_history import track_bot_message
from app.bot.routers.user_routers.main_user_router import main_user_router
from app.bot.routers.user_routers.registration_router import registration_router
from app.bot.routers.user_routers.process_sub import payment_router
from app.bot.routers.user_routers.process_stop_butn import stop_router
from app.bot.routers.user_routers.credit_router import credits_router
from app.bot.routers.user_routers.balance import balance_router
from app.bot.routers.admin_router.main_admin_router import admin_router
from app.config import settings
from loguru import logger

from app.db.dao import UserDAO
from app.db.schemas import TelegramIDModel
from app.db.database import async_session_maker

main_router = Router()

registration_router.message.middleware(CheckPaidSubscription())
payment_router.message.middleware(CheckPaidSubscription())
stop_router.message.middleware(CheckPaidSubscription())
main_user_router.message.middleware(CheckPaidSubscription())
credits_router.message.middleware(CheckPaidSubscription())

registration_router.message.middleware(CheckSub())
payment_router.message.middleware(CheckSub())
stop_router.message.middleware(CheckSub())
main_user_router.message.middleware(CheckSub())
credits_router.message.middleware(CheckSub())

admin_router.message.middleware(CheckAdmin())

main_router.include_router(registration_router)
main_router.include_router(payment_router)
main_router.include_router(stop_router)
main_router.include_router(main_user_router)
main_router.include_router(credits_router)
main_router.include_router(balance_router)
main_router.include_router(admin_router)


class ReferalComment(StatesGroup):
    waiting_comment = State()


@main_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):

    if message.text and message.text.startswith("/start referal_comment_"):
        deal_id = message.text.split("_")[-1]
        await state.update_data(deal_id=deal_id)
        msg = await message.answer("Введите комментарий для клиента:")
        track_bot_message(message.chat.id, msg)
        await state.set_state(ReferalComment.waiting_comment)
        return
    
    await message.answer(messages.get('start'))
    async with async_session_maker() as session:
        user_from_db = await UserDAO.find_one_or_none(session,TelegramIDModel(telegram_id=message.from_user.id))
        if user_from_db:
            await message.answer(f'Привет, {user_from_db.user_enter_first_name}!', reply_markup=MainKeyboard.build_main_kb(message.from_user.id))
            return
    chat_member = await message.bot.get_chat_member(chat_id=settings.CHAT_TO_SUB, user_id=message.from_user.id)
    if chat_member.status == 'left':
        await message.answer("Пожалуйста, подпишитесь на наш канал, чтобы продолжить.", reply_markup=get_subscription_on_chanel_keyboard())
        return

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

@main_user_router.message(F.text == "123123123123123123")
async def test_message(message: Message):
    """
    Тестовая функция для проверки работы бота.
    """
    msg = await message.answer("Тестовое сообщение успешно отправлено!",reply_markup=get_agreement_keyboard())
    track_bot_message(message.chat.id, msg)