"""
Обробники для модуля профілю (клієнтська частина)
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode
from .keyboards import (
    get_profile_main_keyboard,
    get_edit_profile_keyboard,
    get_profile_settings_keyboard,
    get_notifications_settings_keyboard,
    get_language_settings_keyboard,
)
from .states import ProfileStates

# Імпортуємо роутер з __init__.py
from . import profile_router as router


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

    profile_text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація:</b>
• Ім'я: {user.first_name} {user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if user.is_active else "❌ Неактивний"}

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
        "✏️ <b>Редагування профілю</b>\n\nОберіть, що хочете змінити:",
        reply_markup=get_edit_profile_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_first_name")
async def edit_first_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_first_name)
    await callback.message.edit_text(
        "👤 <b>Зміна імені</b>\n\nВведіть нове ім'я:",
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_last_name")
async def edit_last_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_last_name)
    await callback.message.edit_text(
        "👤 <b>Зміна прізвища</b>\n\nВведіть нове прізвище:",
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_phone")
async def edit_phone(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_phone)
    await callback.message.edit_text(
        "📞 <b>Зміна телефону</b>\n\nВведіть новий номер телефону у форматі +380XXXXXXXXX:",
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "profile_settings")
async def profile_settings(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "⚙️ <b>Налаштування профілю</b>\n\nОберіть категорію налаштувань:",
        reply_markup=get_profile_settings_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "edit_notifications")
async def edit_notifications(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    notifications_enabled = data.get("notifications_enabled", True)
    status_text = "✅ Увімкнено" if notifications_enabled else "❌ Вимкнено"
    await callback.message.edit_text(
        f"🔔 <b>Налаштування сповіщень</b>\n\nКеруйте типом сповіщень, які ви хочете отримувати:\n\nСповіщення: {status_text}",
        reply_markup=get_notifications_settings_keyboard(notifications_enabled),
        parse_mode=get_default_parse_mode(),
    )


@router.message(ProfileStates.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if len(new_name) < 2 or len(new_name) > 50:
        await message.answer("❌ Невалідне ім'я. Спробуйте ще раз:")
        return
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
    new_last_name = message.text.strip()
    if len(new_last_name) < 2 or len(new_last_name) > 50:
        await message.answer("❌ Невалідне прізвище. Спробуйте ще раз:")
        return
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
    new_phone = message.text.strip()
    if not new_phone.startswith("+380") or len(new_phone) != 13:
        await message.answer("❌ Неправильний формат телефону. Введіть у форматі +380XXXXXXXXX:")
        return
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if user:
        await db_manager.update_user(user.id, {"phone": new_phone})
        await message.answer(f"✅ Телефон успішно змінено на: {new_phone}")
    else:
        await message.answer("❌ Помилка оновлення профілю")
    await state.clear()
    await profile_command(message)


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_status = data.get("notifications_enabled", True)
    new_status = not current_status
    await state.update_data(notifications_enabled=new_status)
    status_text = "✅ Увімкнено" if new_status else "❌ Вимкнено"
    try:
        await callback.message.edit_text(
            f"🔔 <b>Налаштування сповіщень</b>\n\nКеруйте типом сповіщень, які ви хочете отримувати:\n\nСповіщення: {status_text}",
            reply_markup=get_notifications_settings_keyboard(new_status),
            parse_mode=get_default_parse_mode(),
        )
        await callback.answer(f"Сповіщення: {status_text}")
    except Exception:
        await callback.answer(f"Сповіщення: {status_text}")


@router.callback_query(F.data == "language_settings")
async def language_settings(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🌐 <b>Налаштування мови</b>\n\nОберіть мову інтерфейсу:",
        reply_markup=get_language_settings_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


async def show_profile_for_callback(callback: CallbackQuery):
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Профіль не знайдено!</b>\n\nСпочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return
    profile_text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація:</b>
• Ім'я: {user.first_name} {user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if user.is_active else "❌ Неактивний"}

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
    except Exception:
        await callback.answer()



