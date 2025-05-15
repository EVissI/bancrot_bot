from datetime import datetime, timedelta

from aiogram import Router,F
from aiogram.types import CallbackQuery,PreCheckoutQuery,Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup

from loguru import logger

from app.bot.common.utils import create_bitrix_deal
from app.bot.keyboards.inline_kb import get_subscription_keyboard
from app.db.database import async_session_maker
from app.db.schemas import PromocodeFilterModel, UserFilterModel,UserModel,TelegramIDModel, UserPromocodeFilterModel, UserPromocodeModel
from app.db.dao import PromocodeDAO, UserDAO, UserPromocodeDAO
from app.bot.keyboards.markup_kb import MainKeyboard,BackKeyboard
from app.config import bot,settings
from app.bot.common.msg import messages

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
            if telegram_user.username:
                telegram_link = f"https://t.me/{telegram_user.username}"
            else:
                telegram_link = f"tg://user?id={telegram_user.telegram_id}"
            tg_message = f"Ссылка на телеграмм: {telegram_link}\n"
            date_of_birth = f"Дата рождения: {telegram_user.data_of_birth}\n" if telegram_user.data_of_birth else ''
            region = f"Регион: {telegram_user.region}\n" if telegram_user.region else ''

            comment_msg = f"Оплата подписки: {message.successful_payment.total_amount // 100} {message.successful_payment.currency}\n\
            {tg_message}\
            {date_of_birth}\
            {region}"
        fio = f"{telegram_user.user_enter_last_name} {telegram_user.user_enter_first_name} {telegram_user.user_enter_otchestvo or ''}"
        success, result = await create_bitrix_deal(
                title=f"{fio}_ТГБОТ",
                comment=comment_msg,
                category_id='7',  
                stage_id='C7:UC_CYWJJ2'  # Оплата подписки
            )
        if not success:
            logger.error(f"Failed to create Bitrix deal for payment: {result}")

        await UserDAO.update(session,filters=TelegramIDModel(telegram_id=user_id),values=UserFilterModel.model_validate(telegram_user.to_dict()))
    msg = f"Платеж на сумму {message.successful_payment.total_amount // 100} " f"{message.successful_payment.currency} прошел успешно!\n" + messages.get('after_sub')
    await message.reply(
        msg, reply_markup=MainKeyboard.build_main_kb(message.from_user.id)
    )
    logger.info(f"Получен платеж от {message.from_user.id}")

class EnterPromo(StatesGroup):
    promo = State()

@payment_router.callback_query(F.data.startswith("promo_code"))
async def process_invoice(
    callback: CallbackQuery, state:FSMContext
):
    async with async_session_maker() as session:
        telegram_user = await UserDAO.find_one_or_none(session, TelegramIDModel(telegram_id=callback.from_user.id))
    if telegram_user:
        await callback.message.delete()
        await callback.message.answer('Введите промокод, который вы хотите активировать',reply_markup=BackKeyboard.build_back_kb())
        await state.set_state(EnterPromo.promo)

@payment_router.message(F.text == 'Назад', StateFilter(EnterPromo.promo))
async def process_back(
    message:Message, state:FSMContext
):
    await message.answer('Для работы бота нужно, либо оплатить подписку, либо активировать промокод',reply_markup=get_subscription_keyboard())
    await state.clear()

@payment_router.message(F.text, StateFilter(EnterPromo.promo))
async def process_promo_code(
    message:Message, state:FSMContext
):
    promo_code = message.text
    async with async_session_maker() as session:
        promocode = await PromocodeDAO.find_one_or_none(
            session,
            filters=PromocodeFilterModel(code=promo_code, is_active=True)
        )

    if not promocode:
        await message.answer('Промокод неверный или неактивен')
        await message.answer(
            'Для работы бота нужно, либо оплатить подписку, либо активировать промокод',
            reply_markup=get_subscription_keyboard()
        )
        await state.clear()
        return
    

    if promocode.max_usage and promocode.activate_count >= promocode.max_usage:
        await message.answer('Превышен лимит использования промокода')
        await message.answer(
            'Для работы бота нужно, либо оплатить подписку, либо активировать другой промокод',
            reply_markup=get_subscription_keyboard()
        )
        await state.clear()
        return
    async with async_session_maker() as session:
        user_promocode = await UserPromocodeDAO.find_one_or_none(
            session,
            filters=UserPromocodeFilterModel(
                user_id=message.from_user.id,
                promocode_id=promocode.id
            )
        )

    if user_promocode:
        await message.answer('Вы уже использовали этот промокод')
        await message.answer(
            'Для работы бота нужно, либо оплатить подписку, либо активировать другой промокод',
            reply_markup=get_subscription_keyboard()
        )
        await state.clear()
        return
    async with async_session_maker() as session:
        telegram_user = await UserDAO.find_one_or_none(
            session, 
            TelegramIDModel(telegram_id=message.from_user.id))
    if telegram_user:
        if telegram_user.end_sub_time and telegram_user.end_sub_time > datetime.utcnow():
            telegram_user.end_sub_time += timedelta(days=promocode.discount_days)
        else:
            telegram_user.end_sub_time = datetime.utcnow() + timedelta(days=promocode.discount_days)


        await UserPromocodeDAO.add(
            session,
            UserPromocodeModel(
                user_id=telegram_user.telegram_id,
                promocode_id=promocode.id
            )
        )

        promocode.activate_count += 1
    async with async_session_maker() as session:
        await PromocodeDAO.update(
            session,
            filters=PromocodeFilterModel(id=promocode.id),
            values=PromocodeFilterModel(activate_count=promocode.activate_count)
        )
        
    if telegram_user.username:
        telegram_link = f"https://t.me/{telegram_user.username}"
    else:
        telegram_link = f"tg://user?id={telegram_user.telegram_id}"
    date_of_birth = f"Дата рождения: {telegram_user.data_of_birth}\n" if telegram_user.data_of_birth else ''
    region = f"Регион: {telegram_user.region}\n" if telegram_user.region else ''

    comment_msg = f"Активация промокода: {promo_code}\n\
    Ссылка на телеграм:{telegram_link}\
    {date_of_birth}\
    {region}"
    fio = f"{telegram_user.user_enter_last_name} {telegram_user.user_enter_first_name} {telegram_user.user_enter_otchestvo or ''}"
    success, result = await create_bitrix_deal(
        title=f"{fio}_ТГБОТ",
        comment=comment_msg,
        category_id='7',  # Постбанкротство
        stage_id='C7:NEW'  
    )
    if not success:
        logger.error(f"Failed to create Bitrix deal for promo activation: {result}")
    async with async_session_maker() as session:
        await UserDAO.update(session,filters=TelegramIDModel(telegram_id=message.from_user.id),values=UserFilterModel.model_validate(telegram_user.to_dict()))
    msg = f"Промокод {promo_code} успешно активирован на 6 месяцев!\n" + messages.get('after_sub')
    await message.reply(
        msg, reply_markup=MainKeyboard.build_main_kb(message.from_user.id)
    )
    await state.clear()

