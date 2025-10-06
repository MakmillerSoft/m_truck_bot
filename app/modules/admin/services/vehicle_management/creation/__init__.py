"""
Модуль створення авто для адмін панелі
"""
from aiogram import Router

# Створюємо роутер для модуля створення авто
router = Router()

# Імпортуємо обробники
from .handlers import router as creation_handlers_router

# Включаємо обробники
router.include_router(creation_handlers_router)
