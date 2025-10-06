"""
Сервіс інформаційних сторінок

Цей модуль надає інформаційні сторінки для клієнтів.
Включає інформацію про компанію та контакти.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .company_info import company_info_router
from .contacts import contacts_router

# Створюємо головний роутер для інформації
router = Router()

# Включаємо підроутери
router.include_router(company_info_router)
router.include_router(contacts_router)

# Головний обробник інформації
@router.message(Command("info"))
async def info_command(message: Message):
    """Команда для отримання інформації"""
    # Це буде оброблено модулем company_info
    pass

__all__ = [
    'router',
    'company_info_router',
    'contacts_router'
]

