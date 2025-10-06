"""
Модуль публікації авто в Telegram групу
"""

import logging
from typing import Optional, Dict, Any
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.config.settings import settings
from app.modules.database.models import VehicleModel
from .config import (
    get_topic_for_vehicle_type,
    get_topic_id,
    get_vehicle_emoji,
    get_condition_emoji,
    GroupTopic,
    TOPIC_DISPLAY_NAMES,
)

logger = logging.getLogger(__name__)


class GroupPublisher:
    """Клас для публікації авто в Telegram групу"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.group_chat_id = settings.group_chat_id
        self.group_enabled = settings.group_enabled

    def is_enabled(self) -> bool:
        """Перевірити чи увімкнена публікація в групу"""
        return self.group_enabled and bool(self.group_chat_id)

    def format_vehicle_message(
        self, vehicle: VehicleModel, include_contact: bool = True
    ) -> str:
        """Форматувати повідомлення про авто для групи"""

        # Емодзі для типу та стану
        type_emoji = get_vehicle_emoji(vehicle.vehicle_type.value)
        condition_emoji = get_condition_emoji(vehicle.condition.value)

        # Основна інформація
        message = (
            f"{type_emoji} <b>{vehicle.brand} {vehicle.model}</b> ({vehicle.year})\n\n"
        )

        # Ціна
        message += f"💰 <b>Ціна: ${vehicle.price:,.0f}</b>\n"

        # Стан
        condition_names = {
            "new": "Новий",
            "excellent": "Відмінний",
            "good": "Хороший",
            "fair": "Задовільний",
            "poor": "Поганий",
            "for_parts": "На запчастини",
        }
        condition_name = condition_names.get(
            vehicle.condition.value, vehicle.condition.value
        )
        message += f"{condition_emoji} <b>Стан:</b> {condition_name}\n"

        # Пробіг
        if vehicle.mileage:
            message += f"🛣️ <b>Пробіг:</b> {vehicle.mileage:,} км\n"

        # Місцезнаходження
        if vehicle.location:
            message += f"📍 <b>Місце:</b> {vehicle.location}\n"

        # Технічні характеристики
        if vehicle.engine_type or vehicle.power_hp or vehicle.transmission:
            message += "\n🔧 <b>Технічні характеристики:</b>\n"

            if vehicle.engine_type:
                message += f"• Двигун: {vehicle.engine_type}"
                if vehicle.engine_volume:
                    message += f" ({vehicle.engine_volume}л)"
                message += "\n"

            if vehicle.power_hp:
                message += f"• Потужність: {vehicle.power_hp} к.с.\n"

            if vehicle.transmission:
                message += f"• КПП: {vehicle.transmission}\n"

            if vehicle.fuel_type:
                message += f"• Паливо: {vehicle.fuel_type}\n"

            if vehicle.load_capacity:
                message += f"• Вантажопідйомність: {vehicle.load_capacity} кг\n"

        # Опис
        if vehicle.description:
            message += f"\n📝 <b>Опис:</b>\n{vehicle.description}\n"

        # Контактна інформація
        if include_contact:
            message += f"\n📞 <b>Контакти:</b>\n"
            message += f"• Телефон: {settings.contact_phone}\n"
            message += f"• Email: {settings.contact_email}\n"
            message += f"• Компанія: {settings.company_name}\n"

        # ID авто для внутрішнього використання
        message += f"\n🆔 <code>#{vehicle.id}</code>"

        return message.strip()

    async def publish_vehicle(
        self,
        vehicle: VehicleModel,
        topic: Optional[GroupTopic] = None,
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Опублікувати авто в групу

        Args:
            vehicle: Модель авто для публікації
            topic: Конкретний топік (якщо None - автоматично за типом авто)
            custom_message: Кастомне повідомлення (якщо None - автоматично згенероване)

        Returns:
            Dict з результатом публікації
        """
        result = {
            "success": False,
            "message": "",
            "message_id": None,
            "topic": None,
            "error": None,
        }

        try:
            # Перевірити чи увімкнена публікація
            if not self.is_enabled():
                result["error"] = "Публікація в групу вимкнена або не налаштована"
                return result

            # Визначити топік
            if topic is None:
                topic = get_topic_for_vehicle_type(vehicle.vehicle_type.value)

            result["topic"] = topic.value

            # Підготувати повідомлення
            if custom_message:
                message_text = custom_message
            else:
                message_text = self.format_vehicle_message(vehicle)

            # Отримати ID топіку
            topic_id = get_topic_id(topic)

            # Відправити повідомлення в групу
            if topic_id and topic_id > 0:
                # Відправка в конкретний топік
                sent_message = await self.bot.send_message(
                    chat_id=self.group_chat_id,
                    text=message_text,
                    parse_mode="HTML",
                    message_thread_id=topic_id,
                )
            else:
                # Відправка в загальний чат
                sent_message = await self.bot.send_message(
                    chat_id=self.group_chat_id, text=message_text, parse_mode="HTML"
                )

            result["success"] = True
            result["message"] = (
                f"Авто опубліковано в топік '{TOPIC_DISPLAY_NAMES[topic]}'"
            )
            result["message_id"] = sent_message.message_id

            logger.info(
                f"Vehicle {vehicle.id} published to group {self.group_chat_id}, topic: {topic.value}"
            )

        except TelegramAPIError as e:
            error_msg = f"Помилка Telegram API: {str(e)}"
            result["error"] = error_msg
            logger.error(f"Failed to publish vehicle {vehicle.id}: {error_msg}")

        except Exception as e:
            error_msg = f"Невідома помилка: {str(e)}"
            result["error"] = error_msg
            logger.error(
                f"Unexpected error publishing vehicle {vehicle.id}: {error_msg}"
            )

        return result

    async def test_group_connection(self) -> Dict[str, Any]:
        """Протестувати підключення до групи"""
        result = {"success": False, "message": "", "error": None, "chat_info": None}

        try:
            if not self.is_enabled():
                result["error"] = "Публікація в групу вимкнена або не налаштована"
                return result

            # Отримати інформацію про чат
            chat = await self.bot.get_chat(self.group_chat_id)

            result["success"] = True
            result["message"] = f"Підключення до групи '{chat.title}' успішне"
            result["chat_info"] = {
                "id": chat.id,
                "title": chat.title,
                "type": chat.type,
                "member_count": getattr(chat, "member_count", "Невідомо"),
            }

            logger.info(f"Group connection test successful: {chat.title}")

        except TelegramAPIError as e:
            error_msg = f"Помилка доступу до групи: {str(e)}"
            result["error"] = error_msg
            logger.error(f"Group connection test failed: {error_msg}")

        except Exception as e:
            error_msg = f"Невідома помилка: {str(e)}"
            result["error"] = error_msg
            logger.error(f"Unexpected error testing group connection: {error_msg}")

        return result

    async def send_test_message(
        self, topic: Optional[GroupTopic] = None
    ) -> Dict[str, Any]:
        """Відправити тестове повідомлення в групу"""
        result = {"success": False, "message": "", "message_id": None, "error": None}

        try:
            if not self.is_enabled():
                result["error"] = "Публікація в групу вимкнена або не налаштована"
                return result

            # Визначити топік
            if topic is None:
                topic = GroupTopic.GENERAL

            # Підготувати тестове повідомлення
            test_message = f"""
🧪 <b>Тестове повідомлення M-Truck Bot</b>

📢 Топік: {TOPIC_DISPLAY_NAMES[topic]}
📅 Час відправки: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M')}

✅ Інтеграція з групою працює коректно!

🤖 Повідомлення відправлено з бота автоматично.
"""

            # Отримати ID топіку та відправити
            topic_id = get_topic_id(topic)

            if topic_id and topic_id > 0:
                sent_message = await self.bot.send_message(
                    chat_id=self.group_chat_id,
                    text=test_message.strip(),
                    parse_mode="HTML",
                    message_thread_id=topic_id,
                )
            else:
                sent_message = await self.bot.send_message(
                    chat_id=self.group_chat_id,
                    text=test_message.strip(),
                    parse_mode="HTML",
                )

            result["success"] = True
            result["message"] = (
                f"Тестове повідомлення відправлено в топік '{TOPIC_DISPLAY_NAMES[topic]}'"
            )
            result["message_id"] = sent_message.message_id

            logger.info(
                f"Test message sent to group {self.group_chat_id}, topic: {topic.value}"
            )

        except Exception as e:
            error_msg = f"Помилка відправки тестового повідомлення: {str(e)}"
            result["error"] = error_msg
            logger.error(f"Failed to send test message: {error_msg}")

        return result


# Глобальний екземпляр (буде ініціалізований в main.py)
group_publisher: Optional[GroupPublisher] = None


def init_group_publisher(bot: Bot) -> GroupPublisher:
    """Ініціалізувати глобальний екземпляр GroupPublisher"""
    global group_publisher
    group_publisher = GroupPublisher(bot)
    return group_publisher


def get_group_publisher() -> Optional[GroupPublisher]:
    """Отримати поточний екземпляр GroupPublisher"""
    return group_publisher
