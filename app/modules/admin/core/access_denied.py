"""
Обробники для користувачів без доступу до адмін панелі
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router()

from app.config.settings import settings
from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode
from app.modules.client.services.authentication.registration.keyboards import (
    get_main_menu_inline_keyboard,
)
from ..shared.modules.keyboards.main_keyboards import get_admin_main_keyboard


@router.message(Command("admin"))
async def admin_command_denied(message: Message):
    """Обробка /admin для всіх користувачів: якщо не адмін — пояснення + клієнтське меню,
    якщо адмін — показати головне меню адмін панелі."""

    user_telegram_id = message.from_user.id if message.from_user else None
    is_owner = user_telegram_id in settings.get_admin_ids()
    is_db_admin = False
    try:
        db_user = await db_manager.get_user_by_telegram_id(user_telegram_id) if user_telegram_id else None
        is_db_admin = bool(db_user and getattr(db_user, "role", None) == "admin" or getattr(getattr(db_user, 'role', None), 'value', None) == 'admin')
    except Exception as e:
        logger.error(f"Помилка отримання користувача для /admin: {e}")

    if is_owner or is_db_admin:
        # Показати головне меню адмін панелі
        main_text = (
            """
🏠 <b>Адмін панель M-Truck</b>

Вітаємо в панелі управління ботом!

Оберіть розділ для роботи:
"""
        ).strip()
        await message.answer(
            main_text,
            reply_markup=get_admin_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
        return

    # Не адмін: пояснення + клієнтське меню у новому повідомленні
    denied_text = (
        "❌ <b>Доступ заборонено</b>\n\n"
        "У вас немає прав для доступу до адмін панелі.\n"
        "Якщо вважаєте, що це помилка — зверніться до адміністратора."
    )

    await message.answer(denied_text, parse_mode=get_default_parse_mode())
    await message.answer(
        "Головне меню:",
        reply_markup=get_main_menu_inline_keyboard(),
        parse_mode=get_default_parse_mode(),
    )



@router.callback_query(
    F.data.regexp(r"^(admin_|block_user_|unblock_user_|delete_user_|confirm_block_user_|confirm_unblock_user_|confirm_delete_user_|promote_to_admin_|demote_from_admin_|confirm_promote_to_admin_|confirm_demote_from_admin_|cancel_user_action_|back_to_users_list)")
)
async def admin_callbacks_denied(callback: CallbackQuery):
    """Єдиний обробник: якщо користувач не має доступу, показуємо те саме повідомлення, що і для /admin,
    і виводимо головне меню клієнта у новому повідомленні."""
    user_telegram_id = callback.from_user.id if callback.from_user else None
    is_owner = user_telegram_id in settings.get_admin_ids()
    is_db_admin = False
    try:
        db_user = await db_manager.get_user_by_telegram_id(user_telegram_id) if user_telegram_id else None
        is_db_admin = bool(db_user and getattr(getattr(db_user, 'role', None), 'value', None) == 'admin')
    except Exception as e:
        logger.error(f"Помилка отримання користувача для admin callback: {e}")

    # Якщо адмін/власник — не перехоплюємо (дозволяємо іншим обробникам)
    if is_owner or is_db_admin:
        await callback.answer()
        return

    denied_text = (
        "❌ <b>Доступ заборонено</b>\n\n"
        "У вас немає прав для доступу до адмін панелі.\n"
        "Якщо вважаєте, що це помилка — зверніться до адміністратора."
    )

    try:
        await callback.answer("Доступ заборонено", show_alert=True)
    except Exception:
        pass

    await callback.message.answer(denied_text, parse_mode=get_default_parse_mode())
    await callback.message.answer(
        "Головне меню:",
        reply_markup=get_main_menu_inline_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


# Більш широкий перехоплювач: будь-які callback'и, що містять "admin"
@router.callback_query(F.data.contains("admin"))
async def admin_callbacks_denied_broad(callback: CallbackQuery):
    user_telegram_id = callback.from_user.id if callback.from_user else None
    is_owner = user_telegram_id in settings.get_admin_ids()
    is_db_admin = False
    try:
        db_user = await db_manager.get_user_by_telegram_id(user_telegram_id) if user_telegram_id else None
        is_db_admin = bool(db_user and getattr(getattr(db_user, 'role', None), 'value', None) == 'admin')
    except Exception as e:
        logger.error(f"Помилка отримання користувача для admin callback (broad): {e}")

    if is_owner or is_db_admin:
        await callback.answer()
        return

    denied_text = (
        "❌ <b>Доступ заборонено</b>\n\n"
        "У вас немає прав для доступу до адмін панелі.\n"
        "Якщо вважаєте, що це помилка — зверніться до адміністратора."
    )

    try:
        await callback.answer("Доступ заборонено", show_alert=True)
    except Exception:
        pass

    await callback.message.answer(denied_text, parse_mode=get_default_parse_mode())
    await callback.message.answer(
        "Головне меню:",
        reply_markup=get_main_menu_inline_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


# Перехоплювач для інших адмін-префіксів (vehicle, edit_, search_, publish_, back_to_ всередині адмінки, тощо)
@router.callback_query(
    F.data.regexp(
        r"^(add_vehicle|admin_all_vehicles|admin_quick_search|"
        r"skip_photos_add|skip_photos_replace|edit_vehicle_card|show_publication_options|"
        r"publish_to_bot_only|publish_to_group_only|publish_to_both|back_to_summary_card|"
        r"search_by_parameters|search_by_filter|search_by_id|search_by_vin|search_by_brand|"
        r"search_by_model|search_by_years|search_by_price|back_to_quick_search|"
        r"show_changes_info|edit_field_|edit_field_photos|finish_editing|clear_field_|"
        r"edit_condition_|edit_fuel_|edit_transmission_|edit_location_|edit_photos_add|"
        r"back_to_editing_menu|back_to_vehicle_management|back_to_user_management|users_page_|"
        r"current_page_info|sort_users_|filter_users_status_|view_user_|search_user_by_|"
        r"admin_search_users|back_to_admin_panel|"
        r"select_|back_to_|skip_|add_more_photos|finish_vehicle_creation)"
    )
)
async def admin_callbacks_denied_vehicle_and_users(callback: CallbackQuery):
    user_telegram_id = callback.from_user.id if callback.from_user else None
    is_owner = user_telegram_id in settings.get_admin_ids()
    is_db_admin = False
    try:
        db_user = await db_manager.get_user_by_telegram_id(user_telegram_id) if user_telegram_id else None
        is_db_admin = bool(db_user and getattr(getattr(db_user, 'role', None), 'value', None) == 'admin')
    except Exception as e:
        logger.error(f"Помилка отримання користувача для admin callback (vehicle/users): {e}")

    if is_owner or is_db_admin:
        await callback.answer()
        return

    denied_text = (
        "❌ <b>Доступ заборонено</b>\n\n"
        "У вас немає прав для доступу до адмін панелі.\n"
        "Якщо вважаєте, що це помилка — зверніться до адміністратора."
    )

    try:
        await callback.answer("Доступ заборонено", show_alert=True)
    except Exception:
        pass

    await callback.message.answer(denied_text, parse_mode=get_default_parse_mode())
    await callback.message.answer(
        "Головне меню:",
        reply_markup=get_main_menu_inline_keyboard(),
        parse_mode=get_default_parse_mode(),
    )

