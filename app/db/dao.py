from loguru import logger
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from app.db.base import BaseDAO
from app.db.models import TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession


class UserDAO(BaseDAO[TelegramUser]):
    model = TelegramUser
    