"""
Модуль управління профілем користувача

Цей модуль обробляє управління профілем користувача в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для профілю
profile_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['profile_router']

