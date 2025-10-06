"""
Обробники для користувачів без доступу до адмін панелі
"""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router()

from app.config.settings import settings
from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode
from app.modules.client.services.authentication.registration.keyboards import (
    get_main_menu_inline_keyboard,
)
from ..shared.modules.keyboards.main_keyboards import get_admin_main_keyboard


@router.message(Command("admin"))
async def admin_command_denied(message: Message):
    """Обробка /admin для всіх користувачів: якщо не адмін — пояснення + клієнтське меню,
    якщо адмін — показати головне меню адмін панелі."""

    user_telegram_id = message.from_user.id if message.from_user else None
    is_owner = user_telegram_id in settings.get_admin_ids()
    is_db_admin = False
    try:
        db_user = await db_manager.get_user_by_telegram_id(user_telegram_id) if user_telegram_id else None
        is_db_admin = bool(db_user and getattr(db_user, "role", None) == "admin" or getattr(getattr(db_user, 'role', None), 'value', None) == 'admin')
    except Exception as e:
        logger.error(f"Помилка отримання користувача для /admin: {e}")

    if is_owner or is_db_admin:
        # Показати головне меню адмін панелі
        main_text = (
            """
🏠 <b>Адмін панель M-Truck</b>

Вітаємо в панелі управління ботом!

Оберіть розділ для роботи:
"""
        ).strip()
        await message.answer(
            main_text,
            reply_markup=get_admin_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
        return

    # Не адмін: пояснення + клієнтське меню у новому повідомленні
    denied_text = (
        "❌ <b>Доступ заборонено</b>\n\n"
        "У вас немає прав для доступу до адмін панелі.\n"
        "Якщо вважаєте, що це помилка — зверніться до адміністратора."
    )

    await message.answer(denied_text, parse_mode=get_default_parse_mode())
    await message.answer(
        "Головне меню:",
        reply_markup=get_main_menu_inline_keyboard(),
        parse_mode=get_default_parse_mode(),
    )



