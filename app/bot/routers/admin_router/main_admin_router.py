from aiogram import Router

from app.bot.routers.admin_router.promocodes_router import promocode_router

admin_router = Router()
admin_router.include_router(promocode_router)