"""
Модуль швидкого пошуку авто

Цей модуль обробляє швидкий пошук авто в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для швидкого пошуку
quick_search_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['quick_search_router']

