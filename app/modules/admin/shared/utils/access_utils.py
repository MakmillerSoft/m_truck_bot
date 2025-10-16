"""
Утиліти для перевірки доступу до адмін панелі
"""
import logging
from typing import Optional
from aiogram.types import CallbackQuery, Message

from app.modules.database.manager import db_manager
from app.modules.database.models import UserRole
from app.config.settings import settings

logger = logging.getLogger(__name__)


async def check_admin_access(user_telegram_id: int) -> tuple[bool, Optional[str]]:
    """
    Перевірити, чи має користувач доступ до адмін панелі
    
    Returns:
        tuple: (has_access, reason_if_denied)
    """
    # Перевіряємо, чи користувач засновник
    founder_ids = settings.get_admin_ids()
    if user_telegram_id in founder_ids:
        return True, None
    
    # Перевіряємо роль в БД
    db_user = await db_manager.get_user_by_telegram_id(user_telegram_id)
    if not db_user:
        return False, "Користувач не зареєстрований"
    
    if not db_user.is_active:
        return False, "Користувач заблокований"
    
    if db_user.role == UserRole.ADMIN:
        return True, None
    
    return False, "Недостатньо прав доступу"


async def require_admin_access(callback: CallbackQuery) -> bool:
    """
    Перевірити доступ до адмін панелі для CallbackQuery.
    Якщо доступу немає, відправляє повідомлення і повертає False.
    
    Returns:
        bool: True якщо доступ є, False якщо ні
    """
    has_access, reason = await check_admin_access(callback.from_user.id)
    
    if not has_access:
        logger.warning(f"Користувач {callback.from_user.id} спробував отримати доступ до адмін панелі: {reason}")
        
        await callback.answer(
            f"❌ Доступ заборонено: {reason}",
            show_alert=True
        )
        
        # Перенаправляємо на головне меню клієнта
        from app.modules.client.services.authentication.registration.keyboards import get_main_menu_inline_keyboard
        
        await callback.message.edit_text(
            "🔙 <b>Повернення до головного меню</b>\n\n"
            f"Доступ до адмін панелі заборонено: {reason}",
            reply_markup=get_main_menu_inline_keyboard(),
            parse_mode="HTML"
        )
        
        return False
    
    return True


async def require_admin_access_message(message: Message) -> bool:
    """
    Перевірити доступ до адмін панелі для Message.
    Якщо доступу немає, відправляє повідомлення і повертає False.
    
    Returns:
        bool: True якщо доступ є, False якщо ні
    """
    has_access, reason = await check_admin_access(message.from_user.id)
    
    if not has_access:
        logger.warning(f"Користувач {message.from_user.id} спробував отримати доступ до адмін панелі: {reason}")
        
        await message.answer(
            f"❌ <b>Доступ заборонено</b>\n\n{reason}",
            parse_mode="HTML"
        )
        
        # Перенаправляємо на головне меню клієнта
        from app.modules.client.services.authentication.registration.keyboards import get_main_menu_inline_keyboard
        
        await message.answer(
            "🔙 <b>Повернення до головного меню бота</b>",
            reply_markup=get_main_menu_inline_keyboard(),
            parse_mode="HTML"
        )
        
        return False
    
    return True








