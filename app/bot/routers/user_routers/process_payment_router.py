from datetime import datetime, timedelta
from aiogram import Router,F
from aiogram.types import CallbackQuery,PreCheckoutQuery,Message
from loguru import logger

from app.db.database import async_session_maker
from app.db.schemas import UserFilterModel,UserModel,TelegramIDModel
from app.db.dao import UserDAO
from app.bot.keyboards.markup_kb import MainKeyboard
from app.config import bot,settings

payment_router = Router()

@payment_router.callback_query(F.data.startswith("payment_sub"))
async def process_invoice(
    callback: CallbackQuery
):
    await callback.message.delete()
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Оплата подписки",
        description=f"Оплата подписки на бота",
        payload=f"sub_{callback.from_user.id}_payment",
        provider_token=settings.YO_KASSA_TEL_API_KEY,
        currency="RUB",
        prices=[{"label": "Руб", "amount": 10000}],
    )


@payment_router.pre_checkout_query()
async def process_pre_check_out_query(
    pre_checkout_query: PreCheckoutQuery
):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@payment_router.message(F.successful_payment)
async def process_succesful_payment(message:Message):
    user_id = message.from_user.id
    async with async_session_maker() as session:
        telegram_user = await UserDAO.find_one_or_none(session,TelegramIDModel(telegram_id=user_id))
        if telegram_user:
            if telegram_user.end_sub_time and telegram_user.end_sub_time > datetime.utcnow():
                telegram_user.end_sub_time += timedelta(days=30)
            else:
                telegram_user.end_sub_time = datetime.utcnow() + timedelta(days=30)
        await UserDAO.update(session,filters=TelegramIDModel(telegram_id=user_id),values=UserFilterModel.model_validate(telegram_user.to_dict()))
    await message.reply(
        f"Платеж на сумму {message.successful_payment.total_amount // 100} "
        f"{message.successful_payment.currency} прошел успешно!\n"
        f"Можете свободно пользоваться ботом", reply_markup=MainKeyboard.build_main_kb()
    )
    logger.info(f"Получен платеж от {message.from_user.id}")

