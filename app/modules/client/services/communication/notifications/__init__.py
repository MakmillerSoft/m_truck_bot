"""
Модуль сповіщень

Цей модуль обробляє сповіщення користувачів в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для сповіщень
notifications_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['notifications_router']

