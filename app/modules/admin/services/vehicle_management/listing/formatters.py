"""
Форматування карток авто для адмін панелі
"""
from typing import Optional, Tuple
from app.modules.database.models import VehicleModel
from ..shared.translations import translate_field_value


def format_admin_vehicle_card(vehicle: VehicleModel) -> Tuple[str, Optional[str]]:
    """
    Форматувати картку авто для адмін панелі з умовним відображенням полів
    
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
    
    # Системна інформація
    system_info = []
    
    # Статус авто
    status_text = translate_field_value('status', vehicle.status.value) if vehicle.status else "Наявне"
    system_info.append(f"• <b>Статус:</b> {status_text}")
    
    # Фото
    photo_count = len(vehicle.photos) if vehicle.photos else 0
    system_info.append(f"• <b>Фото:</b> {photo_count} шт.")
    
    # Перегляди
    system_info.append(f"• <b>Перегляди:</b> {vehicle.views_count}")
    
    # Дата створення
    if vehicle.created_at:
        system_info.append(f"• <b>Створено:</b> {vehicle.created_at.strftime('%d.%m.%Y %H:%M')}")
    
    # Дата зміни статусу
    if vehicle.status_changed_at:
        system_info.append(f"• <b>Статус змінено:</b> {vehicle.status_changed_at.strftime('%d.%m.%Y %H:%M')}")
    
    # Дата продажу (тільки якщо статус = sold)
    if vehicle.status and vehicle.status.value == "sold" and vehicle.sold_at:
        system_info.append(f"• <b>Продано:</b> {vehicle.sold_at.strftime('%d.%m.%Y %H:%M')}")
    
    # Статус публікації
    if vehicle.published_in_group or vehicle.published_in_bot:
        published_status = []
        if vehicle.published_in_group:
            published_status.append("група")
        if vehicle.published_in_bot:
            published_status.append("бот")
        system_info.append(f"• <b>Опубліковано:</b> {', '.join(published_status)}")
    
    # Статус публікації в групу
    if vehicle.published_in_group and vehicle.group_message_id:
        # Формуємо посилання на повідомлення в групі
        from app.config.settings import settings
        if settings.group_chat_id:
            group_chat_id = settings.group_chat_id.replace('@', '')
            group_link = f"https://t.me/{group_chat_id}/{vehicle.group_message_id}"
            system_info.append(f"• <b>Посилання в групу:</b> <a href='{group_link}'>Перейти до повідомлення</a>")
        else:
            system_info.append(f"• <b>Посилання в групу:</b> Повідомлення #{vehicle.group_message_id}")
    elif not vehicle.published_in_group:
        system_info.append("• <b>Посилання в групу:</b> Авто не опубліковане в групу")
    
    # Додаємо системну інформацію
    if system_info:
        text += "📊 <b>Системна інформація:</b>\n"
        text += "\n".join(system_info)
    
    # Додаємо ID авто окремо внизу
    text += f"\n\n🆔 <b>ID авто:</b> {vehicle.id}"
    
    # Отримуємо перше фото
    photo_file_id = None
    if vehicle.photos and len(vehicle.photos) > 0:
        photo_file_id = vehicle.photos[0]
        # Перевіряємо валідність file_id
        if not (photo_file_id.startswith("BAAD") or photo_file_id.startswith("AgAC")):
            photo_file_id = None
    
    return text, photo_file_id


def format_vehicle_list_item(vehicle: VehicleModel) -> str:
    """
    Форматувати елемент списку авто для кнопки
    
    Args:
        vehicle: Об'єкт VehicleModel
        
    Returns:
        str: Текст для кнопки
    """
    # Базовий текст
    brand = vehicle.brand or "Без марки"
    text = f"🚛 {brand}"
    
    # Додаємо модель
    if vehicle.model:
        text += f" {vehicle.model}"
    
    # Додаємо рік
    if vehicle.year:
        text += f" ({vehicle.year})"
    
    # Додаємо ціну
    if vehicle.price:
        text += f" - {vehicle.price:,.0f}$"
    
    # Обмежуємо довжину
    if len(text) > 50:
        text = text[:47] + "..."
    
    return text
