"""
Модуль профілю користувача
"""

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode
from .keyboards import (
    get_profile_main_keyboard,
    get_edit_profile_keyboard,
    get_profile_settings_keyboard,
    get_notifications_settings_keyboard,
    get_language_settings_keyboard,
    get_cancel_keyboard,
)
from .states import ProfileStates, SettingsStates

router = Router()


class ProfileStates(StatesGroup):
    """Стани для редагування профілю"""

    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_phone = State()
    waiting_for_notifications = State()


@router.message(F.text == "👤 Профіль")
async def profile_command(message: Message):
    """Показати профіль користувача"""
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(
            "❌ <b>Профіль не знайдено!</b>\n\nСпочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Статус верифікації (завжди True для клієнтів)
    verification_status = "✅ Підтверджено"

    profile_text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація:</b>
• Ім'я: {user.first_name} {user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if user.is_active else "❌ Неактивний"}
• Верифікація: {verification_status}

📞 <b>Контактні дані:</b>
• Телефон: {user.phone or "❌ Не вказано"}
• Telegram ID: {user.telegram_id}

📅 <b>Реєстрація:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}
"""

    await message.answer(
        profile_text.strip(),
        reply_markup=get_profile_main_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: CallbackQuery):
    """Меню редагування профілю"""
    await callback.answer()

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    await callback.message.edit_text(
        "✏️ <b>Редагування профілю</b>\n\n" "Оберіть, що хочете змінити:",
        reply_markup=get_edit_profile_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_first_name")
async def edit_first_name(callback: CallbackQuery, state: FSMContext):
    """Редагування імені"""
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_first_name)

    await callback.message.edit_text(
        "👤 <b>Зміна імені</b>\n\n" "Введіть нове ім'я:",
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_last_name")
async def edit_last_name(callback: CallbackQuery, state: FSMContext):
    """Редагування прізвища"""
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_last_name)

    await callback.message.edit_text(
        "👤 <b>Зміна прізвища</b>\n\n" "Введіть нове прізвище:",
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_phone")
async def edit_phone(callback: CallbackQuery, state: FSMContext):
    """Редагування телефону"""
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_phone)

    await callback.message.edit_text(
        "📞 <b>Зміна телефону</b>\n\n"
        "Введіть новий номер телефону у форматі +380XXXXXXXXX:",
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "profile_settings")
async def profile_settings(callback: CallbackQuery):
    """Налаштування профілю"""
    await callback.answer()

    await callback.message.edit_text(
        "⚙️ <b>Налаштування профілю</b>\n\n" "Оберіть категорію налаштувань:",
        reply_markup=get_profile_settings_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_notifications")
async def edit_notifications(callback: CallbackQuery, state: FSMContext):
    """Налаштування сповіщень"""
    await callback.answer()

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Отримуємо поточний стан з FSM або встановлюємо за замовчуванням
    data = await state.get_data()
    notifications_enabled = data.get(
        "notifications_enabled", True
    )  # За замовчуванням увімкнено

    status_text = "✅ Увімкнено" if notifications_enabled else "❌ Вимкнено"

    await callback.message.edit_text(
        f"🔔 <b>Налаштування сповіщень</b>\n\n"
        f"Керуйте типом сповіщень, які ви хочете отримувати:\n\n"
        f"Сповіщення: {status_text}",
        reply_markup=get_notifications_settings_keyboard(notifications_enabled),
        parse_mode=get_default_parse_mode(),
    )


# Обробники станів
@router.message(ProfileStates.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    """Обробка нового імені"""
    new_name = message.text.strip()

    if len(new_name) < 2:
        await message.answer("❌ Ім'я занадто коротке. Спробуйте ще раз:")
        return

    if len(new_name) > 50:
        await message.answer("❌ Ім'я занадто довге. Спробуйте ще раз:")
        return

    # Оновлюємо в базі даних
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if user:
        await db_manager.update_user(user.id, {"first_name": new_name})
        await message.answer(f"✅ Ім'я успішно змінено на: {new_name}")
    else:
        await message.answer("❌ Помилка оновлення профілю")

    await state.clear()
    await profile_command(message)


@router.message(ProfileStates.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    """Обробка нового прізвища"""
    new_last_name = message.text.strip()

    if len(new_last_name) < 2:
        await message.answer("❌ Прізвище занадто коротке. Спробуйте ще раз:")
        return

    if len(new_last_name) > 50:
        await message.answer("❌ Прізвище занадто довге. Спробуйте ще раз:")
        return

    # Оновлюємо в базі даних
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if user:
        await db_manager.update_user(user.id, {"last_name": new_last_name})
        await message.answer(f"✅ Прізвище успішно змінено на: {new_last_name}")
    else:
        await message.answer("❌ Помилка оновлення профілю")

    await state.clear()
    await profile_command(message)


@router.message(ProfileStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обробка нового телефону"""
    new_phone = message.text.strip()

    # Валідація телефону
    if not new_phone.startswith("+380") or len(new_phone) != 13:
        await message.answer(
            "❌ Неправильний формат телефону. Введіть у форматі +380XXXXXXXXX:"
        )
        return

    # Оновлюємо в базі даних
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if user:
        await db_manager.update_user(user.id, {"phone": new_phone})
        await message.answer(f"✅ Телефон успішно змінено на: {new_phone}")
    else:
        await message.answer("❌ Помилка оновлення профілю")

    await state.clear()
    await profile_command(message)


# Додаткові обробники налаштувань


@router.callback_query(F.data == "language_settings")
async def language_settings(callback: CallbackQuery):
    """Налаштування мови"""
    await callback.answer()

    await callback.message.edit_text(
        "🌐 <b>Налаштування мови</b>\n\n" "Оберіть мову інтерфейсу:",
        reply_markup=get_language_settings_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery, state: FSMContext):
    """Перемикання сповіщень"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Отримуємо поточний стан з FSM або встановлюємо за замовчуванням
    data = await state.get_data()
    current_status = data.get(
        "notifications_enabled", True
    )  # За замовчуванням увімкнено

    # Перемикаємо стан
    new_status = not current_status

    # Зберігаємо новий стан в FSM
    await state.update_data(notifications_enabled=new_status)

    status_text = "✅ Увімкнено" if new_status else "❌ Вимкнено"

    try:
        await callback.message.edit_text(
            f"🔔 <b>Налаштування сповіщень</b>\n\n"
            f"Керуйте типом сповіщень, які ви хочете отримувати:\n\n"
            f"Сповіщення: {status_text}",
            reply_markup=get_notifications_settings_keyboard(new_status),
            parse_mode=get_default_parse_mode(),
        )
        await callback.answer(f"Сповіщення: {status_text}")
    except Exception as e:
        # Якщо повідомлення не змінилося, просто показуємо відповідь
        await callback.answer(f"Сповіщення: {status_text}")


@router.callback_query(F.data == "toggle_new_vehicles_notifications")
async def toggle_new_vehicles_notifications(callback: CallbackQuery, state: FSMContext):
    """Перемикання сповіщень про нові авто"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Отримуємо поточний стан з FSM або встановлюємо за замовчуванням
    data = await state.get_data()
    current_status = data.get(
        "new_vehicles_notifications", True
    )  # За замовчуванням увімкнено

    # Перемикаємо стан
    new_status = not current_status

    # Зберігаємо новий стан в FSM
    await state.update_data(new_vehicles_notifications=new_status)

    status_text = "✅ Увімкнено" if new_status else "❌ Вимкнено"

    await callback.answer(
        f"🚛 Сповіщення про нові авто: {status_text}", show_alert=True
    )


@router.callback_query(F.data == "toggle_requests_notifications")
async def toggle_requests_notifications(callback: CallbackQuery, state: FSMContext):
    """Перемикання сповіщень про заявки"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Отримуємо поточний стан з FSM або встановлюємо за замовчуванням
    data = await state.get_data()
    current_status = data.get(
        "requests_notifications", True
    )  # За замовчуванням увімкнено

    # Перемикаємо стан
    new_status = not current_status

    # Зберігаємо новий стан в FSM
    await state.update_data(requests_notifications=new_status)

    status_text = "✅ Увімкнено" if new_status else "❌ Вимкнено"

    await callback.answer(f"📋 Сповіщення про заявки: {status_text}", show_alert=True)


@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    """Скасувати редагування"""
    await callback.answer()
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Редагування скасовано</b>\n\n" "Повертаємося до профілю...",
        parse_mode=get_default_parse_mode(),
    )

    # Повертаємося до профілю
    await profile_command(callback.message)


async def show_profile_for_callback(callback: CallbackQuery):
    """Показати профіль для callback (для кнопок Назад)"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text(
            "❌ <b>Профіль не знайдено!</b>\n\nСпочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Статус верифікації (завжди True для клієнтів)
    verification_status = "✅ Підтверджено"

    profile_text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація:</b>
• Ім'я: {user.first_name} {user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if user.is_active else "❌ Неактивний"}
• Верифікація: {verification_status}

📞 <b>Контактні дані:</b>
• Телефон: {user.phone or "❌ Не вказано"}
• Telegram ID: {user.telegram_id}

📅 <b>Реєстрація:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}
"""

    try:
        await callback.message.edit_text(
            profile_text.strip(),
            reply_markup=get_profile_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
    except Exception as e:
        # Якщо повідомлення не змінилось, просто відповідаємо на callback
        await callback.answer()
