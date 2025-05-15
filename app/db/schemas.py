from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.db.models import TelegramUser


class TelegramIDModel(BaseModel):
    telegram_id: int

    class Config:
        from_attributes = True


class UserModel(TelegramIDModel):
    username: Optional[str]
    first_name: str
    last_name:Optional[str]
    user_enter_first_name: Optional[str]
    user_enter_last_name: Optional[str]
    user_enter_otchestvo: Optional[str]
    data_of_birth: Optional[str]
    region: Optional[str]
    old_last_name: Optional[str]
    end_sub_time: Optional[datetime]


class UserFilterModel(BaseModel):
    username: Optional[str] = None
    first_name: str = None
    last_name:Optional[str] = None
    user_enter_first_name: Optional[str] = None
    user_enter_last_name: Optional[str] = None
    user_enter_otchestvo: Optional[str] = None
    data_of_birth: Optional[str] = None
    region: Optional[str] = None
    old_last_name: Optional[str] = None
    end_sub_time: Optional[datetime] = None

class PromocodeModel(BaseModel):
    code: str
    discount_days: int
    is_active: bool
    max_usage: Optional[int]
    activate_count: int

    class Config:
        from_attributes = True


class PromocodeFilterModel(BaseModel):
    code: Optional[str] = None
    discount_days: Optional[int] = None
    is_active: Optional[bool] = None
    max_usage: Optional[int] = None
    activate_count: Optional[int] = None


class UserPromocodeModel(BaseModel):
    user_id: int
    promocode_id: int

    class Config:
        from_attributes = True


class UserPromocodeFilterModel(BaseModel):
    user_id: Optional[int] = None
    promocode_id: Optional[int] = None
    