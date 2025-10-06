"""
Модуль підписок на сповіщення

Цей модуль обробляє підписки користувачів на сповіщення про нові авто.
"""

from aiogram import Router

# Створюємо роутер для підписок
subscriptions_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['subscriptions_router']

