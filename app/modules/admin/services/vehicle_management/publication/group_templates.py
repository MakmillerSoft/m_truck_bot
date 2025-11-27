"""
Шаблони карток для публікації в групу
"""
from typing import Dict, Any, List
from app.utils.formatting import get_default_parse_mode
from ..shared.translations import translate_field_value, reverse_translate_field_value
from app.config.settings import settings


def format_group_vehicle_card(data: Dict[str, Any]) -> str:
    """Форматування картки авто для публікації в групу (клієнтський варіант)."""
    
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
    # Форматуємо заголовок (верхній регістр)
    header = f"🚚 <b>{(str(brand or '') + ' ' + str(model or '')).strip().upper()}</b>"
    
    # Збираємо картку
    card_lines = [header, ""]
    
    # Категорія: клікабельна (посилання на топік)
    if vehicle_type:
        ua_type = translate_field_value('vehicle_type', vehicle_type)
        try:
            en_type = reverse_translate_field_value('vehicle_type', vehicle_type)
            topic_id = settings.get_topic_id_for_vehicle_type(en_type)
            if settings.group_chat_id and topic_id:
                group_username = settings.group_chat_id.replace('@', '')
                card_lines.append(f"Категорія: <a href=\"https://t.me/{group_username}?topic={topic_id}\">{ua_type}</a>")
            else:
                card_lines.append(f"Категорія: {ua_type}")
        except Exception:
            card_lines.append(f"Категорія: {ua_type}")
        card_lines.append("")
    
    # 🛠 ТЕХНІЧНІ ХАРАКТЕРИСТИКИ
    main_specs: List[str] = []
    if brand:
        main_specs.append(f"• <b>Марка:</b> {brand}")
    if model:
        main_specs.append(f"• <b>Модель:</b> {model}")
    if year:
        main_specs.append(f"• <b>Рік випуску:</b> {year}")
    if body_type:
        main_specs.append(f"• <b>Тип кузова:</b> {body_type}")
    if condition:
        main_specs.append(f"• <b>Стан:</b> {translate_field_value('condition', condition)}")
    if mileage:
        try:
            main_specs.append(f"• <b>Пробіг:</b> {int(mileage):,} км".replace(',', ' '))
        except Exception:
            main_specs.append(f"• <b>Пробіг:</b> {mileage} км")
    engine_bits: List[str] = []
    if engine_volume:
        engine_bits.append(f"{engine_volume} л")
    if power_hp:
        engine_bits.append(f"{power_hp} кВт")
    if engine_bits:
        main_specs.append(f"• <b>Двигун:</b> {', '.join(engine_bits)}")
    if fuel_type:
        main_specs.append(f"• <b>Тип палива:</b> {translate_field_value('fuel_type', fuel_type)}")
    if transmission:
        main_specs.append(f"• <b>КПП:</b> {translate_field_value('transmission', transmission)}")
    if main_specs:
        card_lines.append("🛠 <b>ТЕХНІЧНІ ХАРАКТЕРИСТИКИ:</b>")
        card_lines.extend(main_specs)
        card_lines.append("")
    
    # Прибираємо решту нестандартних технічних полів для клієнта
    
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
    
    # ФІНАНСУВАННЯ
    card_lines.append("💳 <b>ФІНАНСУВАННЯ:</b>")
    card_lines.append("Консультація: кредит/лізинг")
    card_lines.append("Розрахунок платежів, звертайтесь за номером:")
    card_lines.append("📲 <a href=\"tel:+380502311339\">+380502311339</a>")
    
    card_lines.append("")  # Пустий рядок
    
    # Вартість
    if price:
        try:
            price_text = f"{int(price):,} $".replace(',', ' ')
        except Exception:
            price_text = f"{price} $"
        card_lines.append("💰 <b>Вартість:</b> " + price_text)
    
    # ID авто (обов'язково для менеджерів)
    vehicle_id = data.get('vehicle_id')
    if not vehicle_id:
        # Спробуємо отримати з data['id'] або інших полів
        vehicle_id = data.get('id')
    
    if vehicle_id:
        card_lines.append("")  # Пустий рядок
        card_lines.append(f"🆔 {vehicle_id}")
    
    return "\n".join(card_lines)


def get_vehicle_type_topic_mapping() -> Dict[str, int]:
    """Мапінг типів авто на ID топіків групи"""
    return {
        "Вантажні фургони та рефрижератори": 14,
        "Контейнеровози (з причепами)": 4,
        "Сідельні тягачі та напівпричепи": 18,
        "Змінні кузови": 12,
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
