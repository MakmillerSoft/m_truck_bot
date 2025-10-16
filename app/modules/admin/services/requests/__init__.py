"""
Сервіс для роботи із заявками користувачів (адмін панель)
"""

from aiogram import Router

from .handlers import router as requests_router

router = Router()
router.include_router(requests_router)





