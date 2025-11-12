"""
Обробники перегляду заявок користувачів (адмін панель)
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode
from app.config.settings import settings
from .keyboards import (
    get_requests_main_keyboard,
    get_request_detail_keyboard,
)
from .formatters import (
    format_requests_list,
    format_request_detail,
)

logger = logging.getLogger(__name__)
router = Router()

router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())


@router.message(Command("requests"))
async def open_requests_command(message: Message):
    await show_requests_list(message)


@router.callback_query(F.data.startswith("admin_requests"))
async def open_requests_callback(callback: CallbackQuery, state: FSMContext):
    # Розбір фільтрів із callback_data
    data = callback.data.split(":")
    status_filter = data[1] if len(data) > 1 and data[1] in {"all","new","done","cancelled"} else "all"
    sort = data[2] if len(data) > 2 and data[2] in {"newest","oldest"} else "newest"
    page = int(data[3]) if len(data) > 3 and data[3].isdigit() else 1
    
    # Зберігаємо фільтри в стані для правильної навігації
    await state.update_data(
        requests_status_filter=status_filter,
        requests_sort=sort,
        requests_page=page
    )
    
    await show_requests_list(callback.message, status_filter=status_filter, sort=sort, page=page)


async def show_requests_list(target_message: Message, status_filter: str = "all", sort: str = "newest", page: int = 1):
    per_page = settings.page_size
    total = await db_manager.get_manager_requests_count(status_filter=status_filter)
    stats = await db_manager.get_manager_requests_stats()
    offset = (page - 1) * per_page
    requests = await db_manager.get_manager_requests(status_filter=status_filter, sort=sort, limit=per_page, offset=offset)
    text = format_requests_list(requests, status_filter=status_filter, sort=sort, page=page, total=total, per_page=per_page, stats=stats)
    try:
        await target_message.edit_text(
            text,
            reply_markup=get_requests_main_keyboard(requests, status_filter=status_filter, sort=sort, page=page, total=total, per_page=per_page),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        # message is not modified або інша помилка редагування — оновимо лише клавіатуру
        try:
            await target_message.edit_reply_markup(reply_markup=get_requests_main_keyboard(requests, status_filter=status_filter, sort=sort, page=page, total=total, per_page=per_page))
        except Exception:
            pass


@router.callback_query(F.data.startswith("view_request_"))
async def view_request_detail(callback: CallbackQuery, state: FSMContext):
    try:
        req_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("❌ Невірний ідентифікатор заявки", show_alert=True)
        return

    all_requests = await db_manager.get_manager_requests()
    request = next((r for r in all_requests if r["id"] == req_id), None)
    if not request:
        await callback.answer("❌ Заявку не знайдено", show_alert=True)
        return

    # Зберігаємо поточні фільтри для правильної навігації "Назад"
    current_filters = await state.get_data()
    status_filter = current_filters.get("requests_status_filter", "all")
    sort = current_filters.get("requests_sort", "newest")
    page = current_filters.get("requests_page", 1)

    text = format_request_detail(request)
    await callback.message.edit_text(
        text,
        reply_markup=get_request_detail_keyboard(request, status_filter=status_filter, sort=sort, page=page),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data.startswith("toggle_request_status_"))
async def toggle_request_status(callback: CallbackQuery, state: FSMContext):
    try:
        req_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("❌ Невірний ідентифікатор заявки", show_alert=True)
        return

    # Отримати поточну
    all_requests = await db_manager.get_manager_requests()
    r = next((x for x in all_requests if x["id"] == req_id), None)
    if not r:
        await callback.answer("❌ Заявку не знайдено", show_alert=True)
        return

    # Циклічна зміна статусу: new → done → cancelled → new
    current_status = r.get("status", "new")
    if current_status == "new":
        new_status = "done"
    elif current_status == "done":
        new_status = "cancelled"
    else:  # cancelled
        new_status = "new"
    
    admin_id = callback.from_user.id
    await db_manager.update_manager_request_status(req_id, new_status, admin_id)

    # Отримати збережені фільтри для навігації "Назад"
    current_filters = await state.get_data()
    status_filter = current_filters.get("requests_status_filter", "all")
    sort = current_filters.get("requests_sort", "newest")
    page = current_filters.get("requests_page", 1)

    # Показати оновлену детальну картку
    updated = await db_manager.get_manager_requests()
    r2 = next((x for x in updated if x["id"] == req_id), None)
    text = format_request_detail(r2)
    await callback.message.edit_text(
        text,
        reply_markup=get_request_detail_keyboard(r2, status_filter=status_filter, sort=sort, page=page),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data.startswith("delete_request_"))
async def delete_request_ask(callback: CallbackQuery, state: FSMContext):
    """Запит підтвердження видалення заявки"""
    await callback.answer()
    req_id = int(callback.data.split("_")[-1])

    # Отримати заявку
    all_requests = await db_manager.get_manager_requests()
    r = next((x for x in all_requests if x["id"] == req_id), None)
    if not r:
        await callback.answer("❌ Заявку не знайдено", show_alert=True)
        return

    # Показати підтвердження
    from .keyboards import get_request_delete_confirmation_keyboard
    confirmation_text = (
        "⚠️ <b>Підтвердження видалення</b>\n\n"
        f"Ви впевнені що хочете видалити заявку <b>#{req_id}</b>?\n\n"
        "⚠️ <b>Увага:</b> Цю дію неможливо скасувати!"
    )
    
    # Отримати збережені фільтри
    current_filters = await state.get_data()
    status_filter = current_filters.get("requests_status_filter", "all")
    sort = current_filters.get("requests_sort", "newest")
    page = current_filters.get("requests_page", 1)
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=get_request_delete_confirmation_keyboard(req_id, status_filter, sort, page),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data.startswith("confirm_delete_request_"))
async def confirm_delete_request(callback: CallbackQuery, state: FSMContext):
    """Підтверджене видалення заявки"""
    await callback.answer()
    req_id = int(callback.data.split("_")[-1])

    # Видаляємо заявку з БД
    success = await db_manager.delete_manager_request(req_id)
    
    if not success:
        await callback.answer("❌ Помилка видалення заявки", show_alert=True)
        return
    
    # Повідомляємо про успіх
    await callback.answer("✅ Заявку видалено", show_alert=True)
    
    logger.info(f"✅ Заявку {req_id} видалено адміном {callback.from_user.id}")
    
    # Повертаємо до списку заявок
    current_filters = await state.get_data()
    status_filter = current_filters.get("requests_status_filter", "all")
    sort = current_filters.get("requests_sort", "newest")
    page = current_filters.get("requests_page", 1)
    
    # Викликаємо оновлення списку
    callback.data = f"admin_requests:{status_filter}:{sort}:{page}"
    await open_requests_callback(callback, state)


