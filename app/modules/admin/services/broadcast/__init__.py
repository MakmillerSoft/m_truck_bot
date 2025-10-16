"""
Модуль розсилки (адмін): створення та відправка повідомлень у групу
"""
from aiogram import Router

# Роутер модуля розсилки
broadcast_router = Router(name="admin_broadcast")

# Імпортуємо обробники
from .handlers import router as handlers_router

# Включаємо обробники
broadcast_router.include_router(handlers_router)

__all__ = ["broadcast_router"]



