"""
Модуль розширеного пошуку авто

Цей модуль обробляє розширений пошук авто з фільтрами в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для розширеного пошуку
advanced_search_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['advanced_search_router']

