"""
Модуль експорту даних (адмін)
Експорт даних з БД в Excel
"""
from aiogram import Router

# Роутер модуля експорту
export_router = Router(name="admin_export")

# Імпортуємо обробники
from .handlers import router as handlers_router

# Включаємо обробники
export_router.include_router(handlers_router)

__all__ = ["export_router"]








