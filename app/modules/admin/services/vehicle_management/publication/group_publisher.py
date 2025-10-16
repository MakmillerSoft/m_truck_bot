"""
Модуль публікації авто в групу
"""
import logging
from typing import Dict, Any, List
from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton

from app.config.settings import settings
from .group_templates import (
    format_group_vehicle_card,
    format_media_group_caption,
    get_group_publication_keyboard,
    validate_vehicle_data_for_publication
)

logger = logging.getLogger(__name__)


class GroupPublisher:
    """Клас для публікації авто в групу"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.group_chat_id = settings.group_chat_id
        self.group_enabled = settings.group_enabled
    
    async def publish_vehicle_to_group(self, vehicle_data: Dict[str, Any]) -> tuple[bool, str, int]:
        """
        Публікація авто в групу
        
        Args:
            vehicle_data: Дані про авто
            
        Returns:
            tuple[bool, str, int]: (успіх, повідомлення, message_id)
        """
        try:
            # Логування налаштувань для діагностики
            logger.info(f"🔍 Налаштування групи: chat_id={self.group_chat_id}, enabled={self.group_enabled}")
            
            # Перевірка налаштувань групи
            if not self.group_enabled:
                logger.error("❌ Публікація в групу вимкнена в налаштуваннях")
                return False, "Публікація в групу вимкнена в налаштуваннях", 0
            
            if not self.group_chat_id:
                logger.error("❌ Не налаштовано GROUP_CHAT_ID в .env файлі")
                return False, "Не налаштовано GROUP_CHAT_ID в .env файлі", 0
            
            # Валідація даних
            is_valid, errors = validate_vehicle_data_for_publication(vehicle_data)
            if not is_valid:
                return False, f"Помилка валідації: {'; '.join(errors)}", 0
            
            # Отримуємо фото
            photos = vehicle_data.get('photos', [])
            if not photos:
                return False, "Немає фото для публікації", 0
            
            # Отримуємо ID топіку з налаштувань
            vehicle_type = vehicle_data.get('vehicle_type')
            
            # Перекладаємо українську назву на англійську для отримання топіку
            from ..shared.translations import reverse_translate_field_value
            english_vehicle_type = reverse_translate_field_value('vehicle_type', vehicle_type)
            topic_id = settings.get_topic_id_for_vehicle_type(english_vehicle_type)
            
            logger.info(f"🔍 Публікація: vehicle_type='{vehicle_type}' -> english='{english_vehicle_type}' -> topic_id={topic_id}")
            
            # Форматуємо картку
            card_text = format_group_vehicle_card(vehicle_data)
            
            # Створюємо медіагрупу
            media_group = self._create_media_group(photos, card_text)
            
            # Відправляємо медіагрупу
            media_messages = await self.bot.send_media_group(
                chat_id=self.group_chat_id,
                media=media_group,
                message_thread_id=topic_id
            )
            
            if not media_messages:
                return False, "Не вдалося відправити медіагрупу", 0
            
            # Отримуємо ID першого повідомлення з медіагрупи
            first_message_id = media_messages[0].message_id
            
            # Створюємо кнопку "Написати нам"
            keyboard = get_group_publication_keyboard()
            
            # Відправляємо текст з кнопкою як відповідь на перше повідомлення
            await self.bot.send_message(
                chat_id=self.group_chat_id,
                text="💬 Є питання? Зв'яжіться з нами!",
                reply_to_message_id=first_message_id,
                reply_markup=keyboard,
                message_thread_id=topic_id
            )
            
            logger.info(f"✅ Авто опубліковано в групу {self.group_chat_id}, топік {topic_id}")
            return True, f"Авто успішно опубліковано в групу!", first_message_id
            
        except Exception as e:
            logger.error(f"❌ Помилка публікації в групу: {e}", exc_info=True)
            return False, f"Помилка публікації: {str(e)}", 0
    
    def _create_media_group(self, photos: List[str], caption: str) -> List:
        """Створення медіагрупи з фото/відео із збереженим префіксом video:."""
        media_group: List = []
        for i, raw_id in enumerate(photos):
            is_video = isinstance(raw_id, str) and raw_id.startswith("video:")
            file_id = raw_id.split(":", 1)[1] if is_video else raw_id
            media_caption = caption if i == 0 else None
            if is_video:
                media_group.append(InputMediaVideo(media=file_id, caption=media_caption, parse_mode="HTML"))
            else:
                media_group.append(InputMediaPhoto(media=file_id, caption=media_caption, parse_mode="HTML"))
        return media_group
    
    async def test_group_connection(self) -> tuple[bool, str]:
        """Тест з'єднання з групою"""
        try:
            # Спробуємо отримати інформацію про групу
            chat = await self.bot.get_chat(self.group_chat_id)
            
            if chat:
                return True, f"З'єднання з групою {chat.title} успішне"
            else:
                return False, "Не вдалося отримати інформацію про групу"
                
        except Exception as e:
            logger.error(f"❌ Помилка тесту з'єднання з групою: {e}")
            return False, f"Помилка з'єднання: {str(e)}"
    
    async def get_available_topics(self) -> Dict[str, int]:
        """Отримати доступні топіки групи"""
        try:
            # Отримуємо інформацію про групу
            chat = await self.bot.get_chat(self.group_chat_id)
            
            if hasattr(chat, 'message_thread_id') and chat.message_thread_id:
                # Це супергрупа з топіками
                return {
                    "Сідельні тягачі": 18,
                    "Буси": 16,
                    "Фургони": 14,
                    "Змінні кузови": 12,
                    "Причіпи": 10,
                    "Рефрижератори": 8,
                    "Напівпричепи контейнеровози": 6,
                    "Контейнеровози": 4
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"❌ Помилка отримання топіків: {e}")
            return {}


async def create_group_publisher(bot: Bot) -> GroupPublisher:
    """Створення екземпляру GroupPublisher"""
    return GroupPublisher(bot)

