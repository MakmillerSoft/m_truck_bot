"""
Модуль розсилки (адмін): створення, відправка та історія повідомлень у групу
"""
from aiogram import Router

# Роутер модуля розсилки
broadcast_router = Router(name="admin_broadcast")

# Імпортуємо обробники
from .handlers import router as handlers_router
from .settings import router as settings_router
from .history import router as history_router

# Включаємо обробники
broadcast_router.include_router(handlers_router)
broadcast_router.include_router(settings_router)
broadcast_router.include_router(history_router)

__all__ = ["broadcast_router"]



