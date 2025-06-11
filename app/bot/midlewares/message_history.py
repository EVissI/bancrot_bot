from typing import Dict, Any, Callable, Awaitable
from datetime import datetime
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from loguru import logger


class MessageHistory:
    def __init__(self):
        # Store both user and bot messages
        self.messages: Dict[int, Dict[int, datetime]] = (
            {}
        )  # chat_id -> {message_id -> timestamp}
        self.welcome_messages: Dict[int, int] = {}  # chat_id -> welcome_message_id
        self.ip_result_messages: Dict[int, list[int]] = (
            {}
        )  # chat_id -> list of message_ids

    def add_message(self, user_id: int, message_id: int):
        if user_id not in self.messages:
            self.messages[user_id] = {}
        self.messages[user_id][message_id] = datetime.now()

    def set_welcome_message(self, user_id: int, message_id: int):
        self.welcome_messages[user_id] = message_id

    def add_ip_result(self, user_id: int, message_id: int):
        if user_id not in self.ip_result_messages:
            self.ip_result_messages[user_id] = []
        self.ip_result_messages[user_id].append(message_id)

    def get_messages_to_delete(self, user_id: int) -> list[int]:
        if user_id not in self.messages:
            return []

        current_date = datetime.now()
        to_delete = []
        latest_message = None
        latest_time = datetime.min

        # Находим последнее сообщение дня
        for msg_id, timestamp in self.messages[user_id].items():
            if timestamp.date() == current_date.date() and timestamp > latest_time:
                if latest_message:
                    to_delete.append(latest_message)
                latest_message = msg_id
                latest_time = timestamp
            elif timestamp.date() < current_date.date():
                to_delete.append(msg_id)

        # Не удаляем приветственное сообщение
        if user_id in self.welcome_messages:
            try:
                to_delete.remove(self.welcome_messages[user_id])
            except ValueError:
                pass

        # Не удаляем сообщения с результатами ИП
        if user_id in self.ip_result_messages:
            for ip_msg_id in self.ip_result_messages[user_id]:
                try:
                    to_delete.remove(ip_msg_id)
                except ValueError:
                    pass

        return to_delete


message_history = MessageHistory()


class MessageCleanerMiddleware(BaseMiddleware):
    async def track_bot_response(self, chat_id: int, message: Message) -> None:
        if message and message.message_id:
            message_history.add_message(chat_id, message.message_id)
            if message.text:
                if "Добро пожаловать" in message.text:
                    message_history.set_welcome_message(chat_id, message.message_id)
                elif "Обнаружено исполнительное производство" in message.text:
                    message_history.add_ip_result(chat_id, message.message_id)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        try:
            chat_id = event.chat.id
            bot: Bot = data["bot"]

            # Track user message
            message_history.add_message(chat_id, event.message_id)

            # Store original methods
            original_send_message = bot.send_message
            original_answer = event.answer
            original_reply = event.reply

            # Create wrappers
            async def wrapped_send_message(*args, **kwargs) -> Message:
                message = await original_send_message(*args, **kwargs)
                await self.track_bot_response(chat_id, message)
                return message

            async def wrapped_answer(*args, **kwargs) -> Message:
                message = await original_answer(*args, **kwargs)
                await self.track_bot_response(chat_id, message)
                return message

            async def wrapped_reply(*args, **kwargs) -> Message:
                message = await original_reply(*args, **kwargs)
                await self.track_bot_response(chat_id, message)
                return message

            # Patch methods
            bot.send_message = wrapped_send_message
            event.answer = wrapped_answer
            event.reply = wrapped_reply

            # Process message
            response = await handler(event, data)

            # Restore original methods
            bot.send_message = original_send_message
            event.answer = original_answer
            event.reply = original_reply

            # Track response if it's a Message
            if isinstance(response, Message):
                await self.track_bot_response(chat_id, response)

            # Delete old messages
            try:
                messages_to_delete = message_history.get_messages_to_delete(chat_id)
                logger.debug(f"Messages to delete: {messages_to_delete}")

                for msg_id in messages_to_delete:
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                        if chat_id in message_history.messages:
                            message_history.messages[chat_id].pop(msg_id, None)
                    except TelegramBadRequest as e:
                        if "message to delete not found" in str(e).lower():
                            if chat_id in message_history.messages:
                                message_history.messages[chat_id].pop(msg_id, None)
                        else:
                            logger.error(
                                f"TelegramBadRequest while deleting message {msg_id}: {e}"
                            )
                    except Exception as e:
                        logger.error(f"Failed to delete message {msg_id}: {e}")

            except Exception as e:
                logger.error(f"Error deleting messages: {e}")

            return response

        except Exception as e:
            logger.error(
                f"Global error in MessageCleanerMiddleware: {e}", exc_info=True
            )
            return await handler(event, data)
