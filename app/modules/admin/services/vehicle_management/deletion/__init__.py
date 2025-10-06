"""
Модуль видалення авто для адмін панелі
"""
from aiogram import Router

# Створюємо роутер для модуля видалення авто
router = Router()

# Імпортуємо обробники
from .handlers import router as handlers_router

# Включаємо обробники
router.include_router(handlers_router)
