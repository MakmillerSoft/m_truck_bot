"""
Утиліти для роботи з callback queries в адмін панелі
"""
import logging
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


async def safe_callback_answer(callback: CallbackQuery, text: str = None, show_alert: bool = False):
    """
    Безпечне відповідання на callback query з обробкою застарілих запитів
    
    Args:
        callback: CallbackQuery об'єкт
        text: Текст відповіді (опціонально)
        show_alert: Показувати alert замість toast (опціонально)
    """
    try:
        await callback.answer(text=text, show_alert=show_alert)
    except Exception as e:
        # Ігноруємо помилки застарілих callback queries
        if "query is too old" in str(e) or "query ID is invalid" in str(e):
            logger.warning(f"⚠️ Застарілий callback query ігноровано: {e}")
            return
        raise





