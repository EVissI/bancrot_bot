from datetime import datetime
from typing import Callable, Any, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from app.bot.keyboards.inline_kb import get_subscription_keyboard

from app.db.database import async_session_maker
from app.db.dao import UserDAO
from app.db.schemas import TelegramIDModel,UserFilterModel

class CheckPaidSubscription(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_maker() as session:
            user = await UserDAO.find_one_or_none(session,TelegramIDModel(telegram_id=event.from_user.id))
            
        if user:
            if user.end_sub_time and user.end_sub_time < datetime.utcnow():
                async with async_session_maker() as session:
                    user.end_sub_time = None
                    await UserDAO.update(session, filters=TelegramIDModel(telegram_id=event.from_user.id), values=UserFilterModel.model_validate(user.to_dict()))
                    await event.answer("Ваша подписка истекла. Пожалуйста, продлите её, чтобы продолжить пользоваться ботом.",reply_markup=get_subscription_keyboard())
                    return  
            return await handler(event, data)
        
        return await handler(event, data)