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
        default="+380 66 372 69 41", json_schema_extra={"env": "CONTACT_PHONE"}
    )

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
    
    # Group Topics Configuration - з .env файлу
    topic_saddle_tractors: int = Field(
        default=0, json_schema_extra={"env": "TOPIC_SADDLE_TRACTORS"}
    )
    topic_buses: int = Field(
        default=0, json_schema_extra={"env": "TOPIC_BUSES"}
    )
    topic_vans: int = Field(
        default=0, json_schema_extra={"env": "TOPIC_VANS"}
    )
    topic_variable_body: int = Field(
        default=0, json_schema_extra={"env": "TOPIC_VARIABLE_BODY"}
    )
    topic_trailers: int = Field(
        default=0, json_schema_extra={"env": "TOPIC_TRAILERS"}
    )
    topic_refrigerators: int = Field(
        default=0, json_schema_extra={"env": "TOPIC_REFRIGERATORS"}
    )
    topic_semi_container_carriers: int = Field(
        default=0, json_schema_extra={"env": "TOPIC_SEMI_CONTAINER_CARRIERS"}
    )
    topic_container_carriers: int = Field(
        default=0, json_schema_extra={"env": "TOPIC_CONTAINER_CARRIERS"}
    )

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
        """Отримати ID топіку для типу авто"""
        topic_mapping = {
            'saddle_tractor': self.topic_saddle_tractors,
            'bus': self.topic_buses,
            'van': self.topic_vans,
            'variable_body': self.topic_variable_body,
            'trailer': self.topic_trailers,
            'refrigerator': self.topic_refrigerators,
            'semi_container_carrier': self.topic_semi_container_carriers,
            'container_carrier': self.topic_container_carriers,
        }
        return topic_mapping.get(vehicle_type, 0)


# Глобальний екземпляр налаштувань
settings = Settings()
