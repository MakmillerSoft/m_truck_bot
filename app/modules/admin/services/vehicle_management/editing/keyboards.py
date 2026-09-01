"""
Клавіатури для редагування авто
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from typing import Dict, Any, Optional
from ..shared.translations import translate_field_value


def get_editing_menu_keyboard(vehicle_data: Dict[str, Any], changes: Optional[Dict[str, str]] = None) -> InlineKeyboardMarkup:
    """Клавіатура меню редагування з відображенням змін"""
    buttons = []
    
    # Заголовок з інформацією про зміни
    if changes:
        changes_text = "\n".join([f"✅ {field}: {old} → {new}" for field, (old, new) in changes.items()])
        # Додаємо кнопку з інформацією про зміни (тільки для відображення)
        buttons.append([InlineKeyboardButton(
            text=f"📝 Зміни: {len(changes)}", 
            callback_data="show_changes_info"
        )])
    
    # Поля для редагування (тільки заповнені)
    field_mappings = [
        ("vehicle_type", "🚛 Тип авто", "Тип авто"),
        ("brand", "🏷️ Марка", "Марка"),
        ("model", "🚗 Модель", "Модель"),
        ("vin_code", "🔢 VIN код", "VIN код"),
        ("body_type", "🚚 Тип кузова", "Тип кузова"),
        ("year", "📅 Рік випуску", "Рік випуску"),
        ("condition", "⭐ Стан", "Стан"),
        ("price", "💰 Вартість", "Вартість"),
        ("mileage", "🛣️ Пробіг", "Пробіг"),
        ("fuel_type", "⛽ Тип палива", "Тип палива"),
        ("engine_volume", "🔧 Об'єм двигуна", "Об'єм двигуна"),
        ("power_hp", "⚡ Потужність", "Потужність"),
        ("transmission", "⚙️ Коробка передач", "Коробка передач"),
        ("wheel_radius", "🛞 Радіус коліс", "Радіус коліс"),
        ("load_capacity", "📦 Вантажопідйомність", "Вантажопідйомність"),
        ("total_weight", "⚖️ Загальна маса", "Загальна маса"),
        ("cargo_dimensions", "📏 Габарити вантажного відсіку", "Габарити вантажного відсіку"),
        ("location", "📍 Місцезнаходження", "Місцезнаходження"),
        ("description", "📝 Опис", "Опис"),
    ]
    
    for field_key, emoji_text, display_name in field_mappings:
        value = vehicle_data.get(field_key)
        
        # Показуємо ВСІ поля (заповнені + порожні)
        if value and value != 'Не вказано' and str(value).strip():
            # Заповнене поле - перекладаємо значення для відображення
            translated_value = translate_field_value(field_key, str(value))
            
            # Показуємо зміни якщо поле було змінено
            if changes and field_key in changes:
                old_value, new_value = changes[field_key]
                old_translated = translate_field_value(field_key, str(old_value))
                new_translated = translate_field_value(field_key, str(new_value))
                button_text = f"{emoji_text}: {new_translated} (було: {old_translated})"
            else:
                button_text = f"{emoji_text}: {translated_value}"
        else:
            # Порожнє поле - показуємо як "Не вказано"
            if changes and field_key in changes:
                old_value, new_value = changes[field_key]
                old_translated = translate_field_value(field_key, str(old_value))
                new_translated = translate_field_value(field_key, str(new_value))
                button_text = f"{emoji_text}: {new_translated} (було: {old_translated})"
            else:
                button_text = f"{emoji_text}: [Не вказано]"
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"edit_field_{field_key}"
        )])
    
    # Фото для групи (особливий випадок) - показуємо завжди
    photos = vehicle_data.get('photos', [])
    # Правильно обробляємо photos - може бути список, порожній список, або None
    if isinstance(photos, list) and len(photos) > 0:
        photos_count = len(photos)
        if changes and 'photos' in changes:
            old_count, new_count = changes['photos']
            # Якщо new_count - це список, беремо його довжину
            if isinstance(new_count, list):
                new_count = len(new_count)
            button_text = f"📷 Фото для групи: {new_count} шт. (було: {old_count})"
        else:
            button_text = f"📷 Фото для групи: {photos_count} шт."
    else:
        # Немає фото - показуємо як "Не вказано"
        if changes and 'photos' in changes:
            old_count, new_count = changes['photos']
            # Якщо new_count - це список, беремо його довжину
            if isinstance(new_count, list):
                new_count = len(new_count)
            if isinstance(old_count, list):
                old_count = len(old_count)
            button_text = f"📷 Фото для групи: {new_count} шт. (було: {old_count})"
        else:
            button_text = "📷 Фото для групи: [Не вказано]"
    
    buttons.append([InlineKeyboardButton(
        text=button_text,
        callback_data="edit_field_photos"
    )])
    
    # Головне фото (особливий випадок) - показуємо завжди
    main_photo = vehicle_data.get('main_photo')
    # Правильно обробляємо main_photo - може бути рядок, порожній рядок, або None
    if main_photo and str(main_photo).strip():
        if changes and 'main_photo' in changes:
            old_value, new_value = changes['main_photo']
            button_text = f"🖼️ Головне фото: додано (було: {'додано' if old_value else 'не вказано'})"
        else:
            button_text = "🖼️ Головне фото: додано"
    else:
        # Немає головного фото - показуємо як "Не вказано"
        if changes and 'main_photo' in changes:
            old_value, new_value = changes['main_photo']
            button_text = f"🖼️ Головне фото: {'додано' if new_value else 'не вказано'} (було: {'додано' if old_value else 'не вказано'})"
        else:
            button_text = "🖼️ Головне фото: [Не вказано]"
    
    buttons.append([InlineKeyboardButton(
        text=button_text,
        callback_data="edit_field_main_photo"
    )])
    
    # Кнопка завершення
    buttons.append([InlineKeyboardButton(
        text="✅ Завершити редагування", 
        callback_data="finish_editing"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vehicle_type_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура для вибору типу авто (4 категорії) під час редагування.
    Використовуємо ReplyKeyboard щоб надсилати текстове значення напряму.
    """
    rows = [
        [KeyboardButton(text="Вантажні фургони та рефрижератори")],
        [KeyboardButton(text="Контейнеровози (з причепами)")],
        [KeyboardButton(text="Сідельні тягачі та напівпричепи")],
        [KeyboardButton(text="Змінні кузови")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def get_vehicle_type_inline_keyboard() -> InlineKeyboardMarkup:
    """Інлайн-клавіатура для вибору типу авто (4 категорії) при редагуванні."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚍 Вантажні фургони та рефрижератори", callback_data="edit_type_vans_and_refrigerators")],
            [InlineKeyboardButton(text="🚚 Контейнеровози (з причепами)", callback_data="edit_type_container_carriers")],
            [InlineKeyboardButton(text="🚛 Сідельні тягачі та напівпричепи", callback_data="edit_type_tractors_and_semi")],
            [InlineKeyboardButton(text="🚞 Змінні кузови", callback_data="edit_type_variable_body")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_editing_menu")],
        ]
    )

def get_field_editing_keyboard(field_name: str, current_value: str) -> InlineKeyboardMarkup:
    """Клавіатура для редагування конкретного поля"""
    field_display_names = {
        "vehicle_type": "типу авто",
        "brand": "марки",
        "model": "моделі",
        "vin_code": "VIN коду",
        "body_type": "типу кузова",
        "year": "року випуску",
        "condition": "стану",
        "price": "вартості",
        "mileage": "пробігу",
        "fuel_type": "типу палива",
        "engine_volume": "об'єму двигуна",
        "power_hp": "потужності",
        "transmission": "коробки передач",
        "wheel_radius": "радіуса коліс",
        "load_capacity": "вантажопідйомності",
        "total_weight": "загальної маси",
        "cargo_dimensions": "габаритів",
        "location": "місцезнаходження",
        "description": "опису",
        "photos": "фото для групи",
        "main_photo": "головне фото"
    }
    
    display_name = field_display_names.get(field_name, field_name)
    
    # Для полів з кнопками додаємо inline кнопки
    if field_name == "condition":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🆕 Нове", callback_data="edit_condition_new")],
                [InlineKeyboardButton(text="🔄 Вживане", callback_data="edit_condition_used")],
                [InlineKeyboardButton(text=f"🗑️ Очистити {display_name}", callback_data=f"clear_field_{field_name}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_editing_menu")]
            ]
        )
    elif field_name == "fuel_type":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⛽ Дизель", callback_data="edit_fuel_diesel")],
                [InlineKeyboardButton(text="⛽ Бензин", callback_data="edit_fuel_petrol")],
                [InlineKeyboardButton(text="⛽ Газ", callback_data="edit_fuel_gas")],
                [InlineKeyboardButton(text="⛽ Газ/Бензин", callback_data="edit_fuel_gas_petrol")],
                [InlineKeyboardButton(text="⚡ Електро", callback_data="edit_fuel_electric")],
                [InlineKeyboardButton(text=f"🗑️ Очистити {display_name}", callback_data=f"clear_field_{field_name}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_editing_menu")]
            ]
        )
    elif field_name == "transmission":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🤖 Автоматична", callback_data="edit_transmission_automatic")],
                [InlineKeyboardButton(text="🕹️ Механічна", callback_data="edit_transmission_manual")],
                [InlineKeyboardButton(text="🤖 Робот", callback_data="edit_transmission_robot")],
                [InlineKeyboardButton(text="⚙️ Вариатор", callback_data="edit_transmission_cvt")],
                [InlineKeyboardButton(text=f"🗑️ Очистити {display_name}", callback_data=f"clear_field_{field_name}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_editing_menu")]
            ]
        )
    elif field_name == "location":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏙️ Луцьк", callback_data="edit_location_lutsk")],
                [InlineKeyboardButton(text=f"🗑️ Очистити {display_name}", callback_data=f"clear_field_{field_name}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_editing_menu")]
            ]
        )
    elif field_name == "main_photo":
        # Головне фото - обов'язкове поле, тільки заміна, без очищення
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_editing_menu")]
            ]
        )
    elif field_name == "photos":
        # Фото для групи - обов'язкове поле, тільки заміна, без очищення
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_editing_menu")]
            ]
        )
    else:
        # Для інших полів кнопки "Очистити" та "Назад"
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"🗑️ Очистити {display_name}", 
                    callback_data=f"clear_field_{field_name}"
                )],
                [InlineKeyboardButton(
                    text=f"🔙 Назад", 
                    callback_data="back_to_editing_menu"
                )]
            ]
        )


def get_editing_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура підтвердження завершення редагування"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Так, завершити", callback_data="confirm_finish_editing"),
                InlineKeyboardButton(text="❌ Ні, продовжити", callback_data="back_to_editing_menu")
            ]
        ]
    )


def get_changes_info_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для відображення інформації про зміни"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад до редагування", callback_data="back_to_editing_menu")]
        ]
    )
