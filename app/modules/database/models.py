"""
Моделі бази даних
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """Ролі користувачів"""

    BUYER = "buyer"  # Покупець
    ADMIN = "admin"  # Адміністратор


class VehicleType(str, Enum):
    """Типи вантажних авто"""

    CONTAINER_CARRIER = "container_carrier"  # Контейнеровози
    SEMI_CONTAINER_CARRIER = "semi_container_carrier"  # Напівпричепи контейнеровози
    VARIABLE_BODY = "variable_body"  # Змінні кузови
    SADDLE_TRACTOR = "saddle_tractor"  # Сідельні тягачі
    TRAILER = "trailer"  # Причіпи
    REFRIGERATOR = "refrigerator"  # Рефрижератори
    VAN = "van"  # Фургони
    BUS = "bus"  # Буси


class VehicleCondition(str, Enum):
    """Стан авто"""

    NEW = "new"  # Новий
    USED = "used"  # Вживаний


class VehicleStatus(str, Enum):
    """Статус авто"""
    
    AVAILABLE = "available"  # Наявне
    SOLD = "sold"  # Продане


class ListingStatus(str, Enum):
    """Статус оголошення"""

    ACTIVE = "active"  # Активне
    SOLD = "sold"  # Продано
    RESERVED = "reserved"  # Заброньовано
    INACTIVE = "inactive"  # Неактивне


class UserModel(BaseModel):
    """Модель користувача"""

    id: Optional[int] = None
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.BUYER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class VehicleModel(BaseModel):
    """Модель вантажного авто"""

    id: Optional[int] = None
    vin_code: Optional[str] = None  # Він код
    brand: Optional[str] = None  # Марка
    model: Optional[str] = None  # Модель
    year: Optional[int] = None  # Рік випуску
    vehicle_type: VehicleType  # Тип авто (ОБОВ'ЯЗКОВЕ)
    condition: Optional[VehicleCondition] = None  # Стан
    price: Optional[float] = None  # Ціна в USD
    currency: str = "USD"  # Валюта
    mileage: Optional[int] = None  # Пробіг в км

    # Двигун
    engine_volume: Optional[float] = None  # Об'єм двигуна в л
    power_hp: Optional[int] = None  # Потужність в к.с.
    fuel_type: Optional[str] = None  # Тип палива

    # Трансмісія
    transmission: Optional[str] = None  # Коробка передач

    # Кузов та колісна база
    body_type: Optional[str] = None  # Тип кузова
    wheel_radius: Optional[str] = None  # Радіус коліс

    # Вантажні характеристики
    load_capacity: Optional[int] = None  # Вантажопідйомність в кг
    total_weight: Optional[int] = None  # Загальна маса в кг
    cargo_dimensions: Optional[str] = None  # Габарити вантажного відсіку (ДxШxВ)

    # Додаткова інформація
    location: Optional[str] = None  # Місцезнаходження
    description: Optional[str] = None  # Опис
    photos: List[str] = []  # Список file_id фото для групи
    main_photo: Optional[str] = None  # Головне фото для бота (file_id)

    # Системні поля
    seller_id: int  # ID продавця
    is_active: bool = True  # Активне оголошення
    views_count: int = 0  # Кількість переглядів

    # Поля публікації
    published_at: Optional[datetime] = None  # Дата публікації
    published_in_group: bool = False  # Опубліковано в групу
    published_in_bot: bool = False  # Опубліковано в бот
    group_message_id: Optional[int] = None  # ID повідомлення в групі
    bot_message_id: Optional[int] = None  # ID повідомлення в боті
    
    # Статус авто
    status: VehicleStatus = VehicleStatus.AVAILABLE  # Статус авто (available/sold)
    status_changed_at: Optional[datetime] = None  # Дата зміни статусу
    sold_at: Optional[datetime] = None  # Дата продажу (якщо статус = sold)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ListingModel(BaseModel):
    """Модель оголошення"""

    id: Optional[int] = None
    vehicle_id: int
    seller_id: int
    title: str
    description: Optional[str] = None
    price: float
    is_negotiable: bool = True
    status: ListingStatus = ListingStatus.ACTIVE
    views_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PhotoModel(BaseModel):
    """Модель фото авто"""

    id: Optional[int] = None
    vehicle_id: int
    file_id: str  # Telegram file_id
    file_path: str  # Шлях до файлу
    is_main: bool = False  # Головне фото
    created_at: datetime = Field(default_factory=datetime.now)


class SearchRequestModel(BaseModel):
    """Модель запиту пошуку"""

    id: Optional[int] = None
    user_id: int
    vehicle_type: Optional[VehicleType] = None
    brand: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    max_mileage: Optional[int] = None
    location: Optional[str] = None
    is_saved: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class SavedVehicleModel(BaseModel):
    """Модель збереженого авто покупцем"""

    id: Optional[int] = None
    user_id: int  # ID покупця
    vehicle_id: int  # ID авто
    notes: Optional[str] = None  # Примітки покупця
    created_at: datetime = Field(default_factory=datetime.now)


class ManagerRequestModel(BaseModel):
    """Модель заявки менеджеру"""

    id: Optional[int] = None
    user_id: int
    request_type: str  # buy, finance, service, consultation, other
    details: str  # Деталі запиту
    status: str = "new"  # new, in_progress, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SearchHistoryModel(BaseModel):
    """Модель історії пошуків користувача"""

    id: Optional[int] = None
    user_id: int
    search_name: str  # Назва пошуку (автоматично згенерована)
    vehicle_type: Optional[VehicleType] = None
    brand: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    max_mileage: Optional[int] = None
    location: Optional[str] = None
    engine_type: Optional[str] = None
    fuel_type: Optional[str] = None
    load_capacity: Optional[int] = None
    condition: Optional[VehicleCondition] = None
    results_count: int = 0  # Кількість знайдених результатів
    created_at: datetime = Field(default_factory=datetime.now)


class SubscriptionModel(BaseModel):
    """Модель підписки на сповіщення"""

    id: Optional[int] = None
    user_id: int
    subscription_name: str  # Назва підписки
    vehicle_type: Optional[VehicleType] = None
    brand: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    max_mileage: Optional[int] = None
    location: Optional[str] = None
    engine_type: Optional[str] = None
    fuel_type: Optional[str] = None
    load_capacity: Optional[int] = None
    condition: Optional[VehicleCondition] = None
    is_active: bool = True
    last_notification: Optional[datetime] = None  # Останнє сповіщення
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class GroupTopicModel(BaseModel):
    """Модель гілки групи (forum topic)"""

    id: Optional[int] = None
    thread_id: int
    name: str
    created_at: datetime = Field(default_factory=datetime.now)


class BroadcastModel(BaseModel):
    """Модель розсилки"""

    id: Optional[int] = None
    text: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None
    media_type: Optional[str] = None  # photo | video | media_group
    media_file_id: Optional[str] = None
    media_group_id: Optional[str] = None
    status: str = "draft"  # draft | sent | scheduled
    schedule_period: str = "none"  # none | daily | weekly
    scheduled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
