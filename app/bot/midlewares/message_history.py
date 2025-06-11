from typing import Dict, Any, Callable, Awaitable
from datetime import datetime
from aiogram import BaseMiddleware
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
    async def process_bot_message(self, chat_id: int, message: Message):
        """Helper method to process bot messages"""
        try:
            message_history.add_message(chat_id, message.message_id)

            # Check if it's a welcome message
            if message.text and "Добро пожаловать" in message.text:
                message_history.set_welcome_message(chat_id, message.message_id)

            # Check if it's an IP result message
            if (
                message.text
                and "Обнаружено исполнительное производство" in message.text
            ):
                message_history.add_ip_result(chat_id, message.message_id)
        except Exception as e:
            logger.error(f"Failed to process bot message: {e}")

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        try:
            chat_id = event.chat.id

            # Add user's message to history
            try:
                message_history.add_message(chat_id, event.message_id)
            except Exception as e:
                logger.error(f"Failed to add user message to history: {e}")

            # Process the message with the handler
            response = await handler(event, data)

            # Handle different types of responses
            if isinstance(response, Message):
                await self.process_bot_message(chat_id, response)
            elif isinstance(response, list):
                for msg in response:
                    if isinstance(msg, Message):
                        await self.process_bot_message(chat_id, msg)

            # Get and delete old messages
            try:
                messages_to_delete = message_history.get_messages_to_delete(chat_id)
                logger.debug(f"Messages to delete: {messages_to_delete}")

                for msg_id in messages_to_delete:
                    try:
                        await event.bot.delete_message(
                            chat_id=chat_id, message_id=msg_id
                        )
                        logger.debug(f"Successfully deleted message {msg_id}")
                        # Remove deleted message from history
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
                logger.error(f"Failed to process message deletion: {e}")

            return response

        except Exception as e:
            logger.error(f"Global error in MessageCleanerMiddleware: {e}")
            return await handler(event, data)
