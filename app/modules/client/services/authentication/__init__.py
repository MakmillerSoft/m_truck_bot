"""
Сервіс аутентифікації та управління профілем

Цей модуль надає функціональність аутентифікації для клієнтської частини.
Включає реєстрацію та управління профілем користувача.
"""

from aiogram import Router

from .registration import registration_router
from .profile import profile_router

# Створюємо головний роутер для аутентифікації
router = Router()

# Включаємо підроутери
router.include_router(registration_router)
router.include_router(profile_router)

# Примітка: обробники /start та профілю реалізовано у підмодулях

__all__ = [
    'router',
    'registration_router',
    'profile_router'
]
