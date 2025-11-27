"""
Форматування карток авто для клієнтської частини
"""
from typing import Optional, Tuple
from app.modules.database.models import VehicleModel
from app.modules.admin.services.vehicle_management.shared.translations import translate_field_value


def format_client_vehicle_card(vehicle: VehicleModel) -> Tuple[str, Optional[str]]:
    """Форматування картки авто для клієнта в боті (лише дозволені поля)."""
    # Заголовок (верхній регістр)
    brand = (vehicle.brand or "").strip()
    model = (vehicle.model or "").strip()
    text = f"🚚 <b>{(brand + ' ' + model).strip().upper()}</b>\n\n"

    # Категорія
    text += f"Категорія: {translate_field_value('vehicle_type', vehicle.vehicle_type.value)}\n\n"

    # 🛠 ТЕХНІЧНІ ХАРАКТЕРИСТИКИ
    tech_specs = []
    if brand:
        tech_specs.append(f"• <b>Марка:</b> {brand}")
    if model:
        tech_specs.append(f"• <b>Модель:</b> {model}")
    if vehicle.year:
        tech_specs.append(f"• <b>Рік випуску:</b> {vehicle.year}")
    if vehicle.body_type:
        tech_specs.append(f"• <b>Тип кузова:</b> {vehicle.body_type}")
    if vehicle.condition:
        tech_specs.append(f"• <b>Стан:</b> {translate_field_value('condition', vehicle.condition.value)}")
    if vehicle.mileage:
        try:
            tech_specs.append(f"• <b>Пробіг:</b> {int(vehicle.mileage):,} км".replace(',', ' '))
        except Exception:
            tech_specs.append(f"• <b>Пробіг:</b> {vehicle.mileage} км")
    engine_bits = []
    if vehicle.engine_volume:
        engine_bits.append(f"{vehicle.engine_volume} л")
    if vehicle.power_hp:
        engine_bits.append(f"{vehicle.power_hp} кВт")
    if engine_bits:
        tech_specs.append(f"• <b>Двигун:</b> {', '.join(engine_bits)}")
    if vehicle.fuel_type:
        tech_specs.append(f"• <b>Тип палива:</b> {translate_field_value('fuel_type', vehicle.fuel_type)}")
    if vehicle.transmission:
        tech_specs.append(f"• <b>КПП:</b> {translate_field_value('transmission', vehicle.transmission)}")
    if tech_specs:
        text += "🛠 <b>ТЕХНІЧНІ ХАРАКТЕРИСТИКИ:</b>\n" + "\n".join(tech_specs) + "\n\n"

    # 🔗 ДОДАТКОВО
    additional_info = []
    if vehicle.location:
        additional_info.append(f"• <b>Місцезнаходження:</b> {translate_field_value('location', vehicle.location)}")
    if vehicle.description:
        desc = vehicle.description[:200] + "..." if len(vehicle.description) > 200 else vehicle.description
        additional_info.append(f"• <b>Опис:</b> {desc}")
    if additional_info:
        text += "🔗 <b>ДОДАТКОВО:</b>\n" + "\n".join(additional_info) + "\n\n"

    # 💳 ФІНАНСУВАННЯ
    text += (
        "💳 <b>ФІНАНСУВАННЯ:</b>\n"
        "Консультація: кредит/лізинг\n"
        "Розрахунок платежів, звертайтесь за номером:\n"
        "📲 +380502311339\n\n"
    )

    # 💰 Вартість
    if vehicle.price:
        try:
            price_text = f"{int(vehicle.price):,} $".replace(',', ' ')
        except Exception:
            price_text = f"{vehicle.price} $"
        text += "💰 <b>Вартість:</b> " + price_text + "\n"
    
    # ID авто (обов'язково для менеджерів)
    if vehicle.id:
        text += "\n" + f"🆔 {vehicle.id}"
    
    # Отримуємо головне медіа (фото або відео)
    photo_file_id = None
    if vehicle.main_photo:
        photo_file_id = vehicle.main_photo
        # Перевіряємо валідність file_id
        if not _is_valid_file_id(photo_file_id):
            photo_file_id = None
    elif vehicle.photos and len(vehicle.photos) > 0:
        # Fallback на перший елемент з групи
        photo_file_id = vehicle.photos[0]
        # Перевіряємо валідність file_id
        if not _is_valid_file_id(photo_file_id):
            photo_file_id = None
    
    return text.strip(), photo_file_id


def _is_valid_file_id(file_id: str) -> bool:
    """
    Перевіряє валідність Telegram file_id
    
    Args:
        file_id: Telegram file_id для перевірки
        
    Returns:
        bool: True якщо file_id валідний, False інакше
    """
    if not file_id or not isinstance(file_id, str):
        return False
    
    # Перевіряємо довжину (Telegram file_id зазвичай 20-100 символів)
    if len(file_id) < 10 or len(file_id) > 200:
        return False
    
    # Перевіряємо префікси для різних типів медіа
    valid_prefixes = [
        "BAAD",  # Фото
        "AgAC",  # Фото (альтернативний)
        "BAAE",  # Відео
        "BAAG",  # Відео (альтернативний)
        "CAAE",  # Відео (альтернативний)
        "video:",  # Наш префікс для відео
    ]
    
    # Перевіряємо чи починається з валідного префікса
    for prefix in valid_prefixes:
        if file_id.startswith(prefix):
            return True
    
    # Додаткова перевірка: чи містить тільки допустимі символи
    # Telegram file_id зазвичай містить літери, цифри та деякі спеціальні символи
    import re
    if re.match(r'^[A-Za-z0-9_:.-]+$', file_id):
        return True
    
    return False

