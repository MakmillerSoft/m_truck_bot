"""
Модуль реєстрації користувачів

Цей модуль обробляє процес реєстрації користувачів у клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для реєстрації
registration_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['registration_router']

