"""
Модуль інформації про компанію

Цей модуль обробляє інформаційні сторінки про компанію в клієнтській частині.
"""

from aiogram import Router

# Створюємо роутер для інформації про компанію
company_info_router = Router()

# Імпортуємо обробники
from .handlers import *

__all__ = ['company_info_router']

