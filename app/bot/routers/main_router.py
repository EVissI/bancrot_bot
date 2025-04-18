from app.bot.common.msg import messages
from aiogram import Router,F
from aiogram.filters import CommandStart
from aiogram.types import Message,CallbackQuery

from app.bot.keyboards.inline_kb import get_subscription_on_chanel_keyboard, im_ready
from app.bot.keyboards.markup_kb import MainKeyboard
from app.bot.midlewares.check_sub import CheckSub
from app.bot.midlewares.check_sub_to_bot import CheckPaidSubscription
from app.bot.routers.user_routers.main_user_router import main_user_router
from app.bot.routers.user_routers.registration_router import registration_router
from app.bot.routers.user_routers.process_sub import payment_router
from app.bot.routers.user_routers.process_stop_butn import stop_router
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

registration_router.message.middleware(CheckSub())
payment_router.message.middleware(CheckSub())
stop_router.message.middleware(CheckSub())
main_user_router.message.middleware(CheckSub())

main_router.include_router(registration_router)
main_router.include_router(payment_router)
main_router.include_router(stop_router)
main_router.include_router(main_user_router)

@main_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(messages.get('start'))
    async with async_session_maker() as session:
        user_from_db = await UserDAO.find_one_or_none(session,TelegramIDModel(telegram_id=message.from_user.id))
        if user_from_db:
            await message.answer(f'Привет, {user_from_db.user_enter_first_name}!', reply_markup=MainKeyboard.build_main_kb())
            return
    chat_member = await message.bot.get_chat_member(chat_id=settings.CHAT_TO_SUB, user_id=message.from_user.id)
    if chat_member.status == 'left':
        await message.answer("Пожалуйста, подпишитесь на наш канал, чтобы продолжить.", reply_markup=get_subscription_on_chanel_keyboard())
        return

@main_router.message(F.text == '/test_sub')
async def check_sub(message:Message):
    await message.answer('Пожалуйста, подпишитесь на наш канал, чтобы продолжить.', reply_markup=get_subscription_on_chanel_keyboard())

@main_router.callback_query(F.data.startswith("check_subscription"))
async def check_sub(callback: CallbackQuery):
    chat_member = await callback.message.bot.get_chat_member(settings.CHAT_TO_SUB, callback.message.from_user.id)
    logger.info(chat_member.status)
    if chat_member.status == 'left':
        await callback.message.answer('Упс, кто-то хитрит! Нужно подписаться на канал')
        return
    await callback.message.delete()
    await callback.message.answer('Отлично! Для того чтобы пользоваться ботом, нужно пройти маленькое анкетирование',reply_markup=im_ready())