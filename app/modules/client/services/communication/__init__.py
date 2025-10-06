"""
Сервіс комунікації

Цей модуль надає функціональність комунікації з менеджерами для клієнтів.
Включає заявки менеджерам та сповіщення.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .manager_requests import manager_requests_router
from .notifications import notifications_router

# Створюємо головний роутер для комунікації
router = Router()

# Включаємо підроутери
router.include_router(manager_requests_router)
router.include_router(notifications_router)

# Головний обробник комунікації
@router.message(Command("messages"))
async def messages_command(message: Message):
    """Команда для комунікації з менеджерами"""
    # Це буде оброблено модулем manager_requests
    pass

__all__ = [
    'router',
    'manager_requests_router',
    'notifications_router'
]

