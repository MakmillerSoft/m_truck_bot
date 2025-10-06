"""
Модуль редагування авто
"""
from aiogram import Router
from .handlers import router as editing_router
from .navigation import router as navigation_router

# Створюємо головний роутер модуля
router = Router()

# Підключаємо navigation_router до editing_router
editing_router.include_router(navigation_router)

# Підключаємо editing_router до головного роутера
router.include_router(editing_router)

__all__ = ['router', 'editing_router', 'navigation_router']
