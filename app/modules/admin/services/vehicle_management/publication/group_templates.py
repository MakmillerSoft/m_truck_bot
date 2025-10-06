"""
Шаблони карток для публікації в групу
"""
from typing import Dict, Any, List
from app.utils.formatting import get_default_parse_mode
from ..shared.translations import translate_field_value


def format_group_vehicle_card(data: Dict[str, Any]) -> str:
    """Форматування картки авто для публікації в групу"""
    
    # Отримуємо основні дані
    vehicle_type = data.get('vehicle_type', '')
    brand = data.get('brand', '')
    model = data.get('model', '')
    year = data.get('year', '')
    condition = data.get('condition', '')
    price = data.get('price', '')
    mileage = data.get('mileage', '')
    fuel_type = data.get('fuel_type', '')
    engine_volume = data.get('engine_volume', '')
    power_hp = data.get('power_hp', '')
    transmission = data.get('transmission', '')
    total_weight = data.get('total_weight', '')
    load_capacity = data.get('load_capacity', '')
    wheel_radius = data.get('wheel_radius', '')
    cargo_dimensions = data.get('cargo_dimensions', '')
    body_type = data.get('body_type', '')
    location = data.get('location', '')
    description = data.get('description', '')
    vin_code = data.get('vin_code', '')
    
    # Форматуємо заголовок
    header = f"🚚 <b>{brand} {model}</b>"
    
    # Збираємо картку
    card_lines = [header, ""]
    
    # ОСНОВНІ ХАРАКТЕРИСТИКИ
    main_specs = []
    
    # Категорія
    if vehicle_type:
        translated_vehicle_type = translate_field_value('vehicle_type', vehicle_type)
        main_specs.append(f"<b>Категорія:</b> {translated_vehicle_type}")
    
    # VIN
    if vin_code:
        main_specs.append(f"<b>VIN:</b> {vin_code}")
    
    # Марка
    if brand:
        main_specs.append(f"• <b>Марка:</b> {brand}")
    
    # Модель
    if model:
        main_specs.append(f"• <b>Модель:</b> {model}")
    
    # Рік випуску
    if year:
        main_specs.append(f"• <b>Рік випуску:</b> {year}")
    
    # Тип кузова
    if body_type:
        main_specs.append(f"• <b>Тип кузова:</b> {body_type}")
    
    # Стан
    if condition:
        translated_condition = translate_field_value('condition', condition)
        main_specs.append(f"• <b>Стан:</b> {translated_condition}")
    
    # Пробіг
    if mileage:
        main_specs.append(f"• <b>Пробіг:</b> {mileage} км")
    
    # Додаємо секцію тільки якщо є дані
    if main_specs:
        card_lines.append("📋 <b>ОСНОВНІ ХАРАКТЕРИСТИКИ:</b>")
        card_lines.extend(main_specs)
        card_lines.append("")  # Пустий рядок
    
    # ТЕХНІЧНІ ДАНІ
    tech_specs = []
    
    # Двигун
    engine_info = []
    if engine_volume:
        engine_info.append(f"{engine_volume} л")
    if power_hp:
        engine_info.append(f"{power_hp} к.с.")
    
    if engine_info:
        tech_specs.append(f"• <b>Двигун:</b> {', '.join(engine_info)}")
    
    # Тип палива
    if fuel_type:
        translated_fuel = translate_field_value('fuel_type', fuel_type)
        tech_specs.append(f"• <b>Тип палива:</b> {translated_fuel}")
    
    # КПП
    if transmission:
        translated_transmission = translate_field_value('transmission', transmission)
        tech_specs.append(f"• <b>КПП:</b> {translated_transmission}")
    
    # Загальна маса
    if total_weight:
        tech_specs.append(f"• <b>Загальна маса:</b> {total_weight} кг")
    
    # Вантажопідйомність
    if load_capacity:
        tech_specs.append(f"• <b>Вантажопідйомність:</b> {load_capacity} кг")
    
    # Радіус коліс
    if wheel_radius:
        tech_specs.append(f"• <b>Радіус коліс:</b> {wheel_radius}")
    
    # Габарити вантажного відсіку
    if cargo_dimensions:
        tech_specs.append(f"• <b>Габарити вантажного відсіку:</b> {cargo_dimensions}")
    
    # Додаємо секцію тільки якщо є дані
    if tech_specs:
        card_lines.append("🔧 <b>ТЕХНІЧНІ ДАНІ:</b>")
        card_lines.extend(tech_specs)
        card_lines.append("")  # Пустий рядок
    
    # ДОДАТКОВО
    additional_specs = []
    
    # Місцезнаходження
    if location:
        translated_location = translate_field_value('location', location)
        additional_specs.append(f"• <b>Місцезнаходження:</b> {translated_location}")
    
    # Опис
    if description:
        additional_specs.append(f"• <b>Опис:</b> {description}")
    
    # Додаємо секцію тільки якщо є дані
    if additional_specs:
        card_lines.append("🔗 <b>ДОДАТКОВО:</b>")
        card_lines.extend(additional_specs)
        card_lines.append("")  # Пустий рядок
    
    # Фінансування (завжди відображається)
    card_lines.append("💳 <b>Фінансування (кредит, лізинг)</b>")
    card_lines.append("Отримати консультацію, розрахунок платежів, за номером:")
    card_lines.append("📞 <a href=\"tel:+380502311339\">+380502311339</a>")
    
    card_lines.append("")  # Пустий рядок
    
    # Вартість
    if price:
        card_lines.append(f"💰 <b>Вартість: {price} $</b>")
    
    # ID авто (тільки якщо є)
    vehicle_id = data.get('vehicle_id')
    if vehicle_id:
        card_lines.append("")  # Пустий рядок
        card_lines.append(f"#{vehicle_id}")
    
    return "\n".join(card_lines)


def get_vehicle_type_topic_mapping() -> Dict[str, int]:
    """Мапінг типів авто на ID топіків групи"""
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


def get_topic_id_for_vehicle_type(vehicle_type: str) -> int:
    """Отримати ID топіку для типу авто"""
    mapping = get_vehicle_type_topic_mapping()
    return mapping.get(vehicle_type, 18)  # За замовчуванням - сідельні тягачі


def format_media_group_caption(photos_count: int) -> str:
    """Форматування підпису для медіагрупи"""
    if photos_count == 1:
        return "📷 Фото авто"
    else:
        return f"📷 Фото авто ({photos_count} шт.)"


def get_group_publication_keyboard() -> str:
    """Клавіатура для публікації в групу"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="💬 Написати нам", 
                url="https://t.me/mtruck_finans"
            )]
        ]
    )


def validate_vehicle_data_for_publication(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Валідація даних авто перед публікацією"""
    errors = []
    
    # Обов'язкові поля - тільки тип авто та фото
    if not data.get('vehicle_type') or data.get('vehicle_type') == 'Не вказано':
        errors.append("Поле 'vehicle_type' є обов'язковим")
    
    # Перевірка фото
    photos = data.get('photos', [])
    if not photos or len(photos) == 0:
        errors.append("Потрібно хоча б одне фото")
    
    # Перевірка типу авто
    vehicle_type = data.get('vehicle_type', '')
    if vehicle_type and vehicle_type not in get_vehicle_type_topic_mapping():
        errors.append(f"Невідомий тип авто: {vehicle_type}")
    
    return len(errors) == 0, errors


def get_publication_status_text(success: bool, errors: List[str] = None) -> str:
    """Текст статусу публікації"""
    if success:
        return "✅ Авто успішно опубліковано!"
    else:
        error_text = "\n".join([f"❌ {error}" for error in errors])
        return f"❌ Помилка публікації:\n{error_text}"
