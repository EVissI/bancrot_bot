from typing import Callable, Any, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus

from app.bot.keyboards.inline_kb import get_subscription_on_chanel_keyboard
from app.config import settings
class CheckSub(BaseMiddleware):
    async def __call__(self, 
                       handler: Callable[[Message,Dict[str,Any]], Awaitable[Any]], 
                       event:Message, 
                       data:Dict[str,Any]) -> Any:
        chat_member = await event.bot.get_chat_member(settings.CHAT_TO_SUB, event.from_user.id)
        
        if chat_member.status == 'left':
            await event.answer(
                'Подпишись на канал, чтобы пользоваться ботом',reply_markup=get_subscription_on_chanel_keyboard()
            )
        else:
            return await handler(event,data)