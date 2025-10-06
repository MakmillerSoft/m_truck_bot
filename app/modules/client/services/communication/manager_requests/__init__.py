"""
Модуль заявок менеджеру

Цей модуль обробляє заявки користувачів до менеджерів в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для заявок менеджеру
manager_requests_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['manager_requests_router']

