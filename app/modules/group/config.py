"""
Конфігурація топіків та публікації в Telegram групу
"""

from enum import Enum
from typing import Dict, List


class GroupTopic(str, Enum):
    """Топіки Telegram групи"""

    TRUCKS = "trucks"  # Вантажівки
    SEMI_TRAILERS = "semis"  # Напівпричепи
    VANS = "vans"  # Фургони
    SPECIAL = "special"  # Спецтехніка (самоскиди, крани, міксери)
    TRAILERS = "trailers"  # Причепи
    DEALS = "deals"  # Акції та знижки
    GENERAL = "general"  # Загальний топік


# Мапінг типів авто на топіки групи
VEHICLE_TYPE_TO_TOPIC: Dict[str, GroupTopic] = {
    "truck": GroupTopic.TRUCKS,
    "semi_trailer": GroupTopic.SEMI_TRAILERS,
    "van": GroupTopic.VANS,
    "trailer": GroupTopic.TRAILERS,
    "dump_truck": GroupTopic.SPECIAL,
    "crane": GroupTopic.SPECIAL,
    "mixer": GroupTopic.SPECIAL,
}

# Назви топіків для відображення
TOPIC_DISPLAY_NAMES: Dict[GroupTopic, str] = {
    GroupTopic.TRUCKS: "🚛 Вантажівки",
    GroupTopic.SEMI_TRAILERS: "🚚 Напівпричепи",
    GroupTopic.VANS: "🚐 Фургони",
    GroupTopic.SPECIAL: "🏗️ Спецтехніка",
    GroupTopic.TRAILERS: "🚜 Причепи",
    GroupTopic.DEALS: "💰 Акції",
    GroupTopic.GENERAL: "📢 Загальний",
}

# Емодзі для типів авто
VEHICLE_TYPE_EMOJI: Dict[str, str] = {
    "truck": "🚛",
    "semi_trailer": "🚚",
    "van": "🚐",
    "trailer": "🚜",
    "dump_truck": "🏗️",
    "crane": "🏗️",
    "mixer": "🏗️",
}

# Умови стану авто
CONDITION_EMOJI: Dict[str, str] = {
    "new": "🆕",
    "excellent": "⭐",
    "good": "👍",
    "fair": "👌",
    "poor": "👎",
    "for_parts": "🔧",
}

# ID топіків в групі M-Truck Dev (https://t.me/mtruck_dev)
# Реальні ID топіків з вашої групи
TOPIC_IDS: Dict[GroupTopic, int] = {
    GroupTopic.TRUCKS: 94,  # Гілка 94: https://t.me/mtruck_dev/94
    GroupTopic.SEMI_TRAILERS: 94,  # Гілка 94
    GroupTopic.VANS: 94,  # Гілка 94
    GroupTopic.SPECIAL: 94,  # Гілка 94
    GroupTopic.TRAILERS: 94,  # Гілка 94
    GroupTopic.DEALS: 94,  # Гілка 94
    GroupTopic.GENERAL: 94,  # Гілка 94 (за замовчуванням)
}


# Допоміжні функції для emoji
def get_vehicle_emoji(vehicle_type: str) -> str:
    """Отримати emoji для типу авто"""
    emoji_map = {
        "truck": "🚛",
        "semi_trailer": "🚚",
        "van": "🚐",
        "trailer": "🚛",
        "dump_truck": "🚚",
        "crane": "🏗️",
        "mixer": "🚛",
        "special": "🏗️",
    }
    return emoji_map.get(vehicle_type, "🚛")


def get_condition_emoji(condition: str) -> str:
    """Отримати emoji для стану авто"""
    emoji_map = {
        "new": "✨",
        "excellent": "⭐",
        "good": "👍",
        "fair": "👌",
        "poor": "⚠️",
        "for_parts": "🔧",
    }
    return emoji_map.get(condition, "❔")


def get_topic_for_vehicle_type(vehicle_type: str) -> GroupTopic:
    """Отримати топік групи для типу авто"""
    return VEHICLE_TYPE_TO_TOPIC.get(vehicle_type, GroupTopic.GENERAL)


def get_topic_id(topic: GroupTopic) -> int:
    """Отримати ID топіку в Telegram групі"""
    return TOPIC_IDS.get(topic, TOPIC_IDS[GroupTopic.GENERAL])


def get_vehicle_emoji(vehicle_type: str) -> str:
    """Отримати емодзі для типу авто"""
    return VEHICLE_TYPE_EMOJI.get(vehicle_type, "🚛")


def get_condition_emoji(condition: str) -> str:
    """Отримати емодзі для стану авто"""
    return CONDITION_EMOJI.get(condition, "❔")


def get_all_topics() -> List[Dict[str, str]]:
    """Отримати всі доступні топіки для відображення"""
    topics = []
    for topic in GroupTopic:
        topics.append(
            {
                "id": topic.value,
                "name": TOPIC_DISPLAY_NAMES[topic],
                "topic_id": get_topic_id(topic),
            }
        )
    return topics
