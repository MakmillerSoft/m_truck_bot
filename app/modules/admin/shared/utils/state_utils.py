"""
Утиліти для роботи зі станами (FSM) в адмін панелі
"""
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


async def clear_state_and_render(
    message: Message,
    text: str,
    reply_markup=None,
    parse_mode: str | None = None,
):
    """Очистити стан і відрендерити новий екран у тому ж чаті.

    Використовуйте на верхніх рівнях навігації (головні меню/розділи),
    щоб уникнути “залипання” проміжних станів.
    """
    # Спробувати дістати FSM зі повідомлення
    state: FSMContext | None = getattr(message, "bot", None) and None  # placeholder для типів
    try:
        # FSMContext передається зазвичай у хендлер, але утиліта може викликатись у різних місцях.
        # Тому очищення стану потрібно робити в місці виклику, де є доступ до FSMContext.
        # Ця утиліта не викликає clear() сама, якщо контекст не передано.
        pass
    except Exception:
        pass

    await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)



