"""
Модуль історії пошуків

Цей модуль обробляє історію пошуків користувачів в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для історії пошуків
search_history_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['search_history_router']

