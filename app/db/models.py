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
    privacy_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    used_promocodes:Mapped[list['UserPromocode']] = relationship("UserPromocode", back_populates="user")

class Promocode(Base):
    __tablename__ = 'promocode'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    discount_days: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_usage: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    activate_count: Mapped[int] = mapped_column(Integer, default=None)
    
    users:Mapped["UserPromocode"] = relationship("UserPromocode", back_populates="promocode")


class UserPromocode(Base):
    __tablename__ = 'user_promocode'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True,autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('tel_users.telegram_id'))
    promocode_id: Mapped[int] = mapped_column(Integer, ForeignKey('promocode.id'))
    
    user:Mapped["TelegramUser"]  = relationship("TelegramUser", back_populates="used_promocodes")
    promocode:Mapped["Promocode"]  = relationship("Promocode", back_populates="users")