from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.db.models import TelegramUser
from app.db.schemas import UserFilterModel,TelegramIDModel

async def update_success_fccp():
    async with async_session_maker() as session:
        users:list[TelegramUser] = await UserDAO.find_all(session, filters=UserFilterModel(can_use_fccp=False))
        for user in users:
            user.can_use_fccp = True
            await UserDAO.update(session, filters=TelegramIDModel(telegram_id=user.telegram_id), values=UserFilterModel.model_validate(user.to_dict()))