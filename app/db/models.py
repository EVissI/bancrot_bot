from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Boolean,
    ForeignKey,
    Integer,
    String,
)
from typing import Optional
from app.db.database import Base


class TelegramUser(Base):
    __tablename__ = "tel_users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False,primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String, default=None)
    first_name: Mapped[str] = mapped_column(String, default=None, nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String, default=None)
    user_enter_first_name: Mapped[Optional[str]] = mapped_column(String, default=None)
    user_enter_last_name: Mapped[Optional[str]] = mapped_column(String, default=None)
    user_enter_otchestvo: Mapped[Optional[str]] = mapped_column(String, default=None)
    data_of_birth: Mapped[Optional[str]] = mapped_column(String, default=None)
    region: Mapped[Optional[str]] = mapped_column(String, default=None)
    old_last_name: Mapped[Optional[str]] = mapped_column(String, default=None)
    end_sub_time:Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    activate_free_sub: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
