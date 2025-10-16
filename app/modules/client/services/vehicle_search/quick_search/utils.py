"""
Утиліти для роботи з пошуком авто
"""
import logging

logger = logging.getLogger(__name__)


async def check_group_message_exists(bot, chat_id: str, message_id: int) -> bool:
    """Перевірити існування повідомлення в групі"""
    try:
        # Спочатку перевіряємо доступність групи
        await bot.get_chat(chat_id)
        await bot.get_chat_member(chat_id, bot.id)
        
        # Використовуємо елегантний підхід - спробуємо отримати повідомлення
        # через forward_message в неіснуючий чат (це не створить повідомлення)
        try:
            await bot.forward_message(
                chat_id=-999999999,  # Неіснуючий чат
                from_chat_id=chat_id,
                message_id=message_id,
                disable_notification=True
            )
            
            logger.info(f"✅ Повідомлення {message_id} існує в групі")
            return True
            
        except Exception as forward_error:
            error_message = str(forward_error).lower()
            
            # Перевіряємо різні типи помилок
            if "message to forward not found" in error_message or "message not found" in error_message:
                logger.info(f"❌ Повідомлення {message_id} не знайдено в групі")
                return False
            elif "chat not found" in error_message:
                # Це нормальна поведінка - повідомлення існує, але чат для forward'у не існує
                logger.debug(f"✅ Повідомлення {message_id} існує в групі (перевірка успішна)")
                return True
            else:
                logger.debug(f"⚠️ Невідома помилка при перевірці повідомлення: {forward_error}")
                # На всякий випадок вважаємо що існує
                return True
                
    except Exception as e:
        logger.error(f"❌ Помилка перевірки повідомлення в групі: {e}")
        return False

