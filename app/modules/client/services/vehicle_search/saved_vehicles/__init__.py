"""
Модуль збережених авто

Цей модуль обробляє збережені авто користувачів в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для збережених авто
saved_vehicles_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['saved_vehicles_router']

