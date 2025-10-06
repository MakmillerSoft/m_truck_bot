"""
Middleware для захисту станів FSM
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.utils.formatting import get_default_parse_mode


class StateGuardMiddleware(BaseMiddleware):
    """
    Middleware для захисту від конфліктів станів між модулями
    """

    # Команди що дозволені завжди (незалежно від стану)
    ALWAYS_ALLOWED_COMMANDS = {"/start", "/help", "/cancel", "/stop", "/profile"}

    # Команди що дозволені тільки якщо користувач зареєстрований
    REGISTERED_USER_COMMANDS = {
        "🔍 Пошук авто",
        "📋 Мої збережені",
        "💬 Повідомлення",
        "👤 Профіль",
        "🏢 Про компанію",
        "📞 Контакти",
        "❓ Допомога",
    }

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:

        # Отримати поточний стан
        state: FSMContext = data.get("state")
        if not state:
            return await handler(event, data)

        current_state = await state.get_state()
        message_text = event.text if event.text else ""

        # Дозволити команди що завжди доступні
        if message_text in self.ALWAYS_ALLOWED_COMMANDS:
            # Якщо це /start або /cancel - очистити поточний стан
            if message_text in ["/start", "/cancel"]:
                await state.clear()
            return await handler(event, data)

        # Якщо користувач в процесі реєстрації
        if current_state and current_state.startswith("RegistrationStates"):
            # Дозволити тільки команди реєстрації та завжди дозволені
            if message_text in self.REGISTERED_USER_COMMANDS:
                await event.answer(
                    "⚠️ <b>Спочатку завершіть реєстрацію</b>\n"
                    "Або скасуйте її командою /cancel",
                    parse_mode=get_default_parse_mode(),
                )
                return

        # Якщо користувач в пошуку
        elif current_state and current_state.startswith("SearchStates"):
            # Всі команди дозволені під час пошуку
            pass

        return await handler(event, data)
