"""
Утиліти для форматування повідомлень Telegram
"""

try:
    from aiogram.enums import ParseMode
except ImportError:
    # Fallback для різних версій aiogram
    try:
        from aiogram.types import ParseMode
    except ImportError:
        # Якщо aiogram не встановлений, створюємо заглушку
        class ParseMode:
            HTML = "HTML"


def format_text(text: str) -> str:
    """
    Форматування тексту для Telegram з HTML підтримкою

    Args:
        text: Текст з простими маркерами форматування

    Returns:
        Відформатований текст для HTML parse_mode
    """
    # Замінити ** на HTML bold теги
    text = text.replace("**", "<b>").replace("**", "</b>")

    # Якщо непарна кількість **, виправити
    if text.count("<b>") != text.count("</b>"):
        text = text.replace("<b>", "**").replace("</b>", "**")
        # Конвертувати назад правильно
        parts = text.split("**")
        formatted_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Непарні індекси - жирний текст
                formatted_parts.append(f"<b>{part}</b>")
            else:
                formatted_parts.append(part)
        text = "".join(formatted_parts)

    return text


def get_default_parse_mode() -> ParseMode:
    """Отримати стандартний режим парсингу"""
    return ParseMode.HTML


def clean_text(text: str) -> str:
    """
    Очистити текст від зайвих символів та підготувати для відправки

    Args:
        text: Сирий текст

    Returns:
        Очищений текст
    """
    # Видалити подвійні пробіли
    text = " ".join(text.split())

    # Підготувати для HTML
    text = format_text(text)

    return text


# Готові шаблони повідомлень
WELCOME_MESSAGE = """
🚛 <b>Вітаємо у M-Truck Bot!</b>

Це бот для пошуку та покупки вантажних автомобілів.
Для початку роботи потрібно зареєструватися.

📱 <b>Поділіться вашим номером телефону для зв'язку:</b>
"""

REGISTRATION_SUCCESS = """
✅ <b>Реєстрація успішно завершена!</b>

👋 <b>Вітаємо в нашій спільноті покупців!</b>
☎️ <b>Телефон:</b> {phone}

🚛 Тепер ви можете шукати та обирати вантажні авто!
Використовуйте /help для перегляду всіх можливостей.
"""

PHONE_REQUEST_BUYER = """
👋 <b>Вітаємо, майбутній покупець!</b>

📱 <b>Для завершення реєстрації поділіться номером телефону:</b>
Це потрібно для зв'язку з нашими менеджерами.
"""


def format_vehicle_characteristics(vehicle, main_photo=None) -> str:
    """
    Форматувати характеристики авто без емодзі

    Args:
        vehicle: Об'єкт VehicleModel
        main_photo: Словник з даними головного фото (опціонально)

    Returns:
        Відформатовані характеристики без емодзі
    """
    characteristics = []

    # Основні характеристики (завжди показуємо)
    characteristics.append(f"<b>Рік:</b> {vehicle.year}")
    characteristics.append(f"<b>Ціна:</b> ${vehicle.price:,.0f}")
    characteristics.append(f"<b>Місце:</b> {vehicle.location or 'Не вказано'}")

    # Додаткові характеристики (тільки якщо є)
    if vehicle.mileage and vehicle.mileage > 0:
        characteristics.append(f"<b>Пробіг:</b> {vehicle.mileage:,} км")

    if vehicle.engine_volume and vehicle.engine_volume > 0:
        characteristics.append(f"<b>Об'єм двигуна:</b> {vehicle.engine_volume} л")

    if vehicle.power_hp and vehicle.power_hp > 0:
        characteristics.append(f"<b>Потужність:</b> {vehicle.power_hp} к.с.")

    if vehicle.fuel_type:
        characteristics.append(f"<b>Тип палива:</b> {vehicle.fuel_type}")

    if vehicle.engine_type:
        characteristics.append(f"<b>Двигун:</b> {vehicle.engine_type}")

    if vehicle.transmission:
        characteristics.append(f"<b>КПП:</b> {vehicle.transmission}")

    if vehicle.body_type:
        characteristics.append(f"<b>Тип кузова:</b> {vehicle.body_type}")

    if vehicle.load_capacity and vehicle.load_capacity > 0:
        characteristics.append(
            f"<b>Вантажопідйомність:</b> {vehicle.load_capacity:,} кг"
        )

    if vehicle.total_weight and vehicle.total_weight > 0:
        characteristics.append(f"<b>Загальна маса:</b> {vehicle.total_weight:,} кг")

    if vehicle.cargo_dimensions:
        characteristics.append(
            f"<b>Габарити вантажного відсіку:</b> {vehicle.cargo_dimensions}"
        )

    if vehicle.wheel_radius:
        characteristics.append(f"<b>Радіус коліс:</b> {vehicle.wheel_radius}")


    return "\n".join(characteristics)


def format_vehicle_card_with_photo(vehicle, main_photo=None) -> tuple:
    """
    Форматувати картку авто з фото

    Args:
        vehicle: Об'єкт VehicleModel
        main_photo: Словник з даними головного фото (опціонально)

    Returns:
        tuple: (text, photo_file_id) - текст картки та file_id фото
    """
    # Формуємо текст картки
    text = f"🚛 <b>{vehicle.brand} {vehicle.model}</b>\n\n"

    # Використовуємо утилітну функцію для характеристик без емодзі
    text += format_vehicle_characteristics(vehicle, main_photo)

    if vehicle.description:
        text += f"\n\n📝 <b>Опис:</b>\n{vehicle.description[:200]}{'...' if len(vehicle.description) > 200 else ''}"

    # Повертаємо текст та file_id фото (якщо є та валідний)
    photo_file_id = None
    if main_photo and main_photo.get("file_id"):
        file_id = main_photo.get("file_id")
        # Перевіряємо, чи це валідний Telegram file_id
        if file_id.startswith("BAAD") or file_id.startswith("AgAC"):
            photo_file_id = file_id

    return text, photo_file_id
