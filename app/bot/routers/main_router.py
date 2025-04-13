from aiogram import Router,F
from aiogram.filters import CommandStart
from aiogram.types import Message,CallbackQuery

from app.bot.keyboards.inline_kb import get_subscription_on_chanel_keyboard, im_ready
from app.bot.midlewares.check_sub import CheckSub
from app.bot.routers.user_routers.main_user_router import main_user_router
from app.bot.routers.user_routers.registration_router import registration_router
from app.bot.routers.user_routers.process_payment_router import payment_router
from app.bot.routers.user_routers.process_stop_butn import stop_router
from app.config import settings
from loguru import logger

main_router = Router()
main_router.include_router(registration_router)
main_router.include_router(payment_router)
main_router.include_router(stop_router)
main_router.include_router(main_user_router)

@main_router.message(CommandStart())
async def cmd_start(message: Message):
    chat_member = await message.bot.get_chat_member(settings.CHAT_TO_SUB, message.from_user.id)
    if chat_member.status == 'left':
        await message.answer("Привет! Пожалуйста, подпишитесь на наш канал, чтобы продолжить.", reply_markup=get_subscription_on_chanel_keyboard())
        return
    await message.answer('Отлично! Я вижу ты подписан на наш канал, пройди акнкетирование, чтобы пользоваться ботом',reply_markup=im_ready())

@main_router.callback_query(F.data.startswith("check_subscription"))
async def check_sub(callback: CallbackQuery):
    chat_member = await callback.message.bot.get_chat_member(settings.CHAT_TO_SUB, callback.message.from_user.id)
    logger.info(chat_member.status)
    if chat_member.status == 'left':
        await callback.message.answer('Упс, кто-то хитрит! Нужно подписаться на канал')
        return
    await callback.message.delete()
    await callback.message.answer('Отлично! Для того чтобы пользоваться ботом, нужно пройти маленькое анкетирование',reply_markup=im_ready())