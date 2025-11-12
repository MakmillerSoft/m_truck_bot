"""
Налаштування додатку - читає тільки з .env файлу
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    """Основні налаштування додатку"""

    # Telegram Bot Configuration
    bot_token: str = Field(..., json_schema_extra={"env": "BOT_TOKEN"})

    # Admin Configuration
    admin_ids: str = Field(default="", json_schema_extra={"env": "ADMIN_IDS"})

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./data/truck_bot.db",
        json_schema_extra={"env": "DATABASE_URL"},
    )

    # Application Configuration
    debug: bool = Field(default=False, json_schema_extra={"env": "DEBUG"})
    log_level: str = Field(default="INFO", json_schema_extra={"env": "LOG_LEVEL"})

    # Business Configuration
    company_name: str = Field(
        default="M-Truck Company", json_schema_extra={"env": "COMPANY_NAME"}
    )
    contact_phone: str = Field(
        default="+380502311339", json_schema_extra={"env": "CONTACT_PHONE"}
    )
    
    # Pagination Configuration
    page_size: int = Field(
        default=10, json_schema_extra={"env": "PAGE_SIZE"}
    )  # Кількість елементів на сторінці в усіх розділах

    # FSM Storage Configuration
    fsm_storage_type: str = Field(
        default="memory", json_schema_extra={"env": "FSM_STORAGE_TYPE"}
    )  # memory, redis
    redis_url: str = Field(
        default="redis://localhost:6379/1", json_schema_extra={"env": "REDIS_URL"}
    )

    # Telegram Group Configuration - БЕЗ значень за замовчуванням
    group_chat_id: str = Field(
        default="", json_schema_extra={"env": "GROUP_CHAT_ID"}
    )  # ID або @username групи
    group_enabled: bool = Field(
        default=False, json_schema_extra={"env": "GROUP_ENABLED"}
    )  # Чи увімкнена публікація в групу
    
    # Group Topics Configuration - 4 категорії для публікації авто
    topic_tractors_and_semi: int = Field(
        default=18, json_schema_extra={"env": "TOPIC_TRACTORS_AND_SEMI"}
    )  # Сідельні тягачі та напівпричепи
    topic_vans_and_refrigerators: int = Field(
        default=14, json_schema_extra={"env": "TOPIC_VANS_AND_REFRIGERATORS"}
    )  # Вантажні фургони та рефрижератори
    topic_variable_body: int = Field(
        default=12, json_schema_extra={"env": "TOPIC_VARIABLE_BODY"}
    )  # Змінні кузови
    topic_container_carriers: int = Field(
        default=4, json_schema_extra={"env": "TOPIC_CONTAINER_CARRIERS"}
    )  # Контейнеровози (з причепами)

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # Дозволити додаткові поля
    )

    def get_admin_ids(self) -> List[int]:
        """Отримати список ID адміністраторів як integer"""
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]
    
    def get_topic_id_for_vehicle_type(self, vehicle_type: str) -> int:
        """Отримати ID топіку для типу авто
        
        Мапінг 8 типів авто на 4 топіки групи:
        - Сідельні тягачі та напівпричепи → TOPIC_TRACTORS_AND_SEMI
        - Вантажні фургони та рефрижератори → TOPIC_VANS_AND_REFRIGERATORS
        - Змінні кузови → TOPIC_VARIABLE_BODY
        - Контейнеровози (з причепами) → TOPIC_CONTAINER_CARRIERS
        """
        topic_mapping = {
            # Сідельні тягачі та напівпричепи (thread_id: 18)
            'saddle_tractor': self.topic_tractors_and_semi,
            'semi_container_carrier': self.topic_tractors_and_semi,
            
            # Вантажні фургони та рефрижератори (thread_id: 14)
            'van': self.topic_vans_and_refrigerators,
            'refrigerator': self.topic_vans_and_refrigerators,
            
            # Змінні кузови (thread_id: 12)
            'variable_body': self.topic_variable_body,
            
            # Контейнеровози (з причепами) (thread_id: 4)
            'container_carrier': self.topic_container_carriers,
            'trailer': self.topic_container_carriers,
            
            # Буси (не використовується, але для зворотної сумісності)
            'bus': self.topic_tractors_and_semi,  # або можна залишити 0
        }
        return topic_mapping.get(vehicle_type, self.topic_tractors_and_semi)


# Глобальний екземпляр налаштувань
settings = Settings()
