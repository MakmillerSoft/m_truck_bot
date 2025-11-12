"""
Модуль публікації авто в бот
"""
import logging
from typing import Dict, Any, List, TYPE_CHECKING
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.modules.database.manager import DatabaseManager

if TYPE_CHECKING:
    from app.modules.database.models import VehicleModel
from .group_templates import (
    format_group_vehicle_card,
    validate_vehicle_data_for_publication
)

logger = logging.getLogger(__name__)


class BotPublisher:
    """Клас для публікації авто в бот"""
    
    def __init__(self, bot: Bot, db_manager: DatabaseManager):
        self.bot = bot
        self.db_manager = db_manager
    
    async def publish_vehicle_to_bot(self, vehicle_data: Dict[str, Any], user_id: int) -> tuple[bool, str, int]:
        """
        Публікація авто в бот (збереження в БД)
        
        Args:
            vehicle_data: Дані про авто
            user_id: ID користувача-адміністратора
            
        Returns:
            tuple[bool, str, int]: (успіх, повідомлення, ID авто)
        """
        try:
            # Валідація даних
            is_valid, errors = validate_vehicle_data_for_publication(vehicle_data)
            if not is_valid:
                return False, f"Помилка валідації: {'; '.join(errors)}", 0
            
            # Підготовка даних для БД
            vehicle_model = self._prepare_vehicle_model(vehicle_data, user_id)
            
            # Збереження в БД
            vehicle_id = await self.db_manager.create_vehicle(vehicle_model)
            
            if not vehicle_id:
                return False, "Не вдалося зберегти авто в базу даних", 0
            
            logger.info(f"✅ Авто збережено в БД з ID: {vehicle_id}")
            return True, f"Авто успішно збережено в бот! ID: {vehicle_id}", vehicle_id
            
        except Exception as e:
            logger.error(f"❌ Помилка публікації в бот: {e}", exc_info=True)
            return False, f"Помилка збереження: {str(e)}", 0
    
    def _prepare_vehicle_model(self, vehicle_data: Dict[str, Any], user_id: int) -> 'VehicleModel':
        """Підготовка VehicleModel для збереження в БД"""
        from app.modules.database.models import VehicleModel, VehicleType, VehicleCondition
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 _prepare_vehicle_model: отримані дані: {vehicle_data}")
        
        # Переклади для типів і станів (UA -> EN)
        from ..shared.translations import reverse_translate_field_value
        
        # Отримуємо типи
        vehicle_type_str = vehicle_data.get('vehicle_type', '')
        condition_str = vehicle_data.get('condition', '')
        
        logger.info(f"🔍 _prepare_vehicle_model: vehicle_type_str='{vehicle_type_str}', condition_str='{condition_str}'")
        
        # ВАЛІДАЦІЯ ОБОВ'ЯЗКОВИХ ПОЛІВ (тип авто, головне фото та фото для групи)
        if not vehicle_type_str:
            raise ValueError("Поле 'vehicle_type' є обов'язковим")
        
        main_photo = vehicle_data.get('main_photo')
        photos = vehicle_data.get('photos', [])
        
        if not main_photo and (not photos or len(photos) == 0):
            raise ValueError("Потрібно хоча б одне фото (головне або для групи)")
        
        # Для необов'язкових полів встановлюємо значення за замовчуванням
        brand = vehicle_data.get('brand') or 'Не вказано'
        model = vehicle_data.get('model') or 'Не вказано'
        year = self._safe_int(vehicle_data.get('year'))
        if year == 0:
            year = None  # Якщо рік не вказаний, встановлюємо None
        
        # Стан авто через зворотний переклад
        condition_en = reverse_translate_field_value('condition', condition_str) if condition_str else None
        try:
            condition = VehicleCondition(condition_en) if condition_en else VehicleCondition.USED
        except Exception:
            condition = VehicleCondition.USED
        price = self._safe_float(vehicle_data.get('price'))
        if price == 0.0:
            price = None  # Якщо ціна не вказана, встановлюємо None
        
        # Тип авто через зворотний переклад 4-ох категорій до представницького EN
        vehicle_type_en = reverse_translate_field_value('vehicle_type', vehicle_type_str)
        try:
            vehicle_type = VehicleType(vehicle_type_en)
        except Exception:
            raise ValueError(f"Невідомий тип авто: {vehicle_type_str}")
        
        logger.info(f"🔍 _prepare_vehicle_model: vehicle_type={vehicle_type}, condition={condition}")
        
        # Створюємо VehicleModel (БЕЗ engine_type - поле видалено!)
        vehicle_model = VehicleModel(
            seller_id=user_id,
            vehicle_type=vehicle_type,
            brand=brand,
            model=model,
            vin_code=vehicle_data.get('vin_code'),
            body_type=vehicle_data.get('body_type'),
            year=year,
            condition=condition,
            price=price,
            mileage=self._safe_int(vehicle_data.get('mileage')),
            fuel_type=vehicle_data.get('fuel_type', ''),
            engine_volume=self._safe_float(vehicle_data.get('engine_volume')),
            power_hp=self._safe_int(vehicle_data.get('power_hp')),
            transmission=vehicle_data.get('transmission', ''),
            wheel_radius=vehicle_data.get('wheel_radius', ''),
            load_capacity=self._safe_int(vehicle_data.get('load_capacity')),
            total_weight=self._safe_int(vehicle_data.get('total_weight')),
            cargo_dimensions=vehicle_data.get('cargo_dimensions', ''),
            location=vehicle_data.get('location', ''),
            description=vehicle_data.get('description', ''),
            photos=vehicle_data.get('photos', []),
            main_photo=vehicle_data.get('main_photo'),
            published_in_bot=True,  # Позначаємо як опубліковане в бот
            is_active=True
        )
        
        return vehicle_model
    
    def _safe_int(self, value: Any) -> int:
        """Безпечне перетворення в int"""
        if value is None or value == 'Не вказано' or value == '':
            return 0
        
        try:
            if isinstance(value, str):
                # Видаляємо всі нецифрові символи
                cleaned = ''.join(filter(str.isdigit, str(value)))
                return int(cleaned) if cleaned else 0
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value: Any) -> float:
        """Безпечне перетворення в float"""
        if value is None or value == 'Не вказано' or value == '':
            return 0.0
        
        try:
            if isinstance(value, str):
                # Замінюємо кому на крапку та видаляємо зайві символи
                cleaned = str(value).replace(',', '.').replace(' ', '')
                # Видаляємо всі символи крім цифр, крапки та мінуса
                cleaned = ''.join(c for c in cleaned if c.isdigit() or c in '.-')
                return float(cleaned) if cleaned else 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def format_bot_vehicle_card(self, vehicle_data: Dict[str, Any]) -> str:
        """Форматування картки авто для відображення в боті"""
        return format_group_vehicle_card(vehicle_data)
    
    def get_bot_vehicle_keyboard(self, vehicle_id: int) -> InlineKeyboardMarkup:
        """Клавіатура для картки авто в боті"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💾 Зберегти", callback_data=f"save_vehicle_{vehicle_id}")],
                [InlineKeyboardButton(text="💬 Написати нам", url="https://t.me/mtruck_finans")],
                [InlineKeyboardButton(text="👁️ Переглянути", callback_data=f"view_vehicle_{vehicle_id}")]
            ]
        )


async def create_bot_publisher(bot: Bot, db_manager: DatabaseManager) -> BotPublisher:
    """Створення екземпляру BotPublisher"""
    return BotPublisher(bot, db_manager)
