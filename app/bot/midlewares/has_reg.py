from datetime import datetime
from typing import Callable, Any, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from app.bot.keyboards.inline_kb import get_subscription_keyboard, im_ready

from app.db.database import async_session_maker
from app.db.dao import UserDAO
from app.db.schemas import TelegramIDModel,UserFilterModel

class HasReg(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_maker() as session:
            user = await UserDAO.find_one_or_none(session,TelegramIDModel(telegram_id=event.from_user.id))
            logger.info(user.username)
            if not user.privacy_accepted:
                await event.answer("Для пользования этим функционалом, вам необходимо пройти регистрацию.",reply_markup=im_ready())
                return
            else:
                return await handler(event,data)