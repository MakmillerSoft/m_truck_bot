"""
Форматування карток авто для клієнтської частини
"""
from typing import Optional, Tuple
from app.modules.database.models import VehicleModel
from app.modules.admin.services.vehicle_management.shared.translations import translate_field_value


def format_client_vehicle_card(vehicle: VehicleModel) -> Tuple[str, Optional[str]]:
    """
    Форматувати картку авто для клієнтської частини (БЕЗ системної інформації)
    
    Args:
        vehicle: Об'єкт VehicleModel
        
    Returns:
        tuple: (text, photo_file_id) - текст картки та file_id першого фото
    """
    # Заголовок
    brand = vehicle.brand or "Без марки"
    model = vehicle.model or "Без моделі"
    text = f"🚛 <b>{brand} {model}</b>\n\n"
    
    # Основні характеристики (тільки заповнені)
    main_specs = []
    
    # Тип авто (завжди є)
    main_specs.append(f"• <b>Тип:</b> {translate_field_value('vehicle_type', vehicle.vehicle_type.value)}")
    
    # Рік
    if vehicle.year:
        main_specs.append(f"• <b>Рік:</b> {vehicle.year}")
    
    # Стан
    if vehicle.condition:
        main_specs.append(f"• <b>Стан:</b> {translate_field_value('condition', vehicle.condition.value)}")
    
    # Ціна
    if vehicle.price:
        main_specs.append(f"• <b>Ціна:</b> {vehicle.price:,.0f} $")
    
    # Пробіг
    if vehicle.mileage:
        main_specs.append(f"• <b>Пробіг:</b> {vehicle.mileage:,} км")
    
    # Додаємо основні характеристики
    if main_specs:
        text += "📋 <b>Основні характеристики:</b>\n"
        text += "\n".join(main_specs) + "\n\n"
    
    # Технічні дані (тільки заповнені)
    tech_specs = []
    
    # Двигун
    engine_info = []
    if vehicle.engine_volume:
        engine_info.append(f"{vehicle.engine_volume} л")
    if vehicle.power_hp:
        engine_info.append(f"{vehicle.power_hp} к.с.")
    
    if engine_info:
        tech_specs.append(f"• <b>Двигун:</b> {', '.join(engine_info)}")
    
    # Тип палива
    if vehicle.fuel_type:
        tech_specs.append(f"• <b>Паливо:</b> {translate_field_value('fuel_type', vehicle.fuel_type)}")
    
    # КПП
    if vehicle.transmission:
        tech_specs.append(f"• <b>КПП:</b> {translate_field_value('transmission', vehicle.transmission)}")
    
    # Тип кузова
    if vehicle.body_type:
        tech_specs.append(f"• <b>Тип кузова:</b> {vehicle.body_type}")
    
    # Радіус коліс
    if vehicle.wheel_radius:
        tech_specs.append(f"• <b>Радіус коліс:</b> {vehicle.wheel_radius}")
    
    # Додаємо технічні дані
    if tech_specs:
        text += "🔧 <b>Технічні дані:</b>\n"
        text += "\n".join(tech_specs) + "\n\n"
    
    # Вантажні характеристики (тільки заповнені)
    cargo_specs = []
    
    # Вантажопідйомність
    if vehicle.load_capacity:
        cargo_specs.append(f"• <b>Вантажопідйомність:</b> {vehicle.load_capacity:,} кг")
    
    # Загальна маса
    if vehicle.total_weight:
        cargo_specs.append(f"• <b>Загальна маса:</b> {vehicle.total_weight:,} кг")
    
    # Габарити
    if vehicle.cargo_dimensions:
        cargo_specs.append(f"• <b>Габарити:</b> {vehicle.cargo_dimensions}")
    
    # Додаємо вантажні характеристики
    if cargo_specs:
        text += "📦 <b>Вантажні характеристики:</b>\n"
        text += "\n".join(cargo_specs) + "\n\n"
    
    # Додаткова інформація (тільки заповнена)
    additional_info = []
    
    # Місцезнаходження
    if vehicle.location:
        additional_info.append(f"• <b>Місцезнаходження:</b> {translate_field_value('location', vehicle.location)}")
    
    # VIN код
    if vehicle.vin_code:
        additional_info.append(f"• <b>VIN:</b> {vehicle.vin_code}")
    
    # Опис
    if vehicle.description:
        # Обмежуємо довжину опису
        description = vehicle.description[:200] + "..." if len(vehicle.description) > 200 else vehicle.description
        additional_info.append(f"• <b>Опис:</b> {description}")
    
    # Додаємо додаткову інформацію
    if additional_info:
        text += "📍 <b>Додатково:</b>\n"
        text += "\n".join(additional_info) + "\n\n"
    
    # СИСТЕМНА ІНФОРМАЦІЯ ПРИБРАНА ДЛЯ КЛІЄНТІВ
    
    # Отримуємо головне медіа (фото або відео)
    photo_file_id = None
    if vehicle.main_photo:
        photo_file_id = vehicle.main_photo
    elif vehicle.photos and len(vehicle.photos) > 0:
        # Fallback на перший елемент з групи
        photo_file_id = vehicle.photos[0]
    
    return text.strip(), photo_file_id

