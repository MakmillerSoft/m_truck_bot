"""
Модуль швидкого пошуку авто
"""
from aiogram import Router

# Створюємо роутер для модуля швидкого пошуку
router = Router()

# Імпортуємо обробники
from .handlers import router as handlers_router

# Включаємо обробники
router.include_router(handlers_router)