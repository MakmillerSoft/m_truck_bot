"""
Middleware для блокування доступу заблокованим користувачам
"""
from typing import Any, Awaitable, Callable, Dict

import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode


logger = logging.getLogger(__name__)


class ActiveUserGuardMiddleware(BaseMiddleware):
    """Блокує доступ користувачам з is_active = False.

    Правила:
    - Якщо користувача немає в БД → пропускаємо (може реєструватися)
    - Якщо користувач є та is_active = False → показуємо повідомлення і зупиняємо обробку
    - Інакше пропускаємо
    """

    BLOCKED_TEXT = (
        "❌ <b>Ваш доступ заблоковано</b>\n\n"
        "Зверніться до адміністратора, якщо вважаєте це помилкою."
    )

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        telegram_user = event.from_user if hasattr(event, "from_user") else None
        if telegram_user is None:
            return await handler(event, data)

        try:
            user = await db_manager.get_user_by_telegram_id(telegram_user.id)
        except Exception as e:
            logger.error(f"Помилка отримання користувача: {e}")
            return await handler(event, data)

        # Якщо користувача немає — дозволяємо реєстрацію
        if not user:
            return await handler(event, data)

        # Якщо користувач заблокований — блокуємо будь-яку взаємодію
        if user and not getattr(user, "is_active", True):
            if isinstance(event, Message):
                await event.answer(self.BLOCKED_TEXT, parse_mode=get_default_parse_mode())
            else:
                await event.answer()
                await event.message.answer(self.BLOCKED_TEXT, parse_mode=get_default_parse_mode())
            return

        return await handler(event, data)



