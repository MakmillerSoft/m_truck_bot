"""
Модуль контактів

Цей модуль обробляє контактну інформацію в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для контактів
contacts_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['contacts_router']

