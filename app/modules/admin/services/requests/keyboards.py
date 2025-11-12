from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_requests_main_keyboard(requests: list, status_filter: str = "all", sort: str = "newest", page: int = 1, total: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """Клавіатура зі списком заявок у стилі блоку 'Всі авто'"""
    rows = []
    
    # Визначаємо наступний статус для циклічного перемикання
    if status_filter == "all":
        next_status = "new"
    elif status_filter == "new":
        next_status = "done"
    elif status_filter == "done":
        next_status = "cancelled"
    else:  # cancelled
        next_status = "all"
    
    # Кнопки сортування (2 кнопки в 1 рядок) у стилі "Всі авто"
    sort_buttons = [
        InlineKeyboardButton(
            text="📅 Дата ↓" if sort in ("newest", "date_desc") else "📅 Дата ↑" if sort in ("oldest", "date_asc") else "📅 Дата",
            callback_data=f"admin_requests:{status_filter}:{'oldest' if sort in ('newest','date_desc') else 'newest'}:{page}"
        ),
        InlineKeyboardButton(
            text=f"📋 {'Всі' if status_filter=='all' else ('Нові' if status_filter=='new' else ('Опрацьовані' if status_filter=='done' else 'Скасовані'))}",
            callback_data=f"admin_requests:{next_status}:{sort}:{page}"
        ),
    ]
    rows.append(sort_buttons)
    
    # Список заявок (кожна в окремому ряду, як список авто)
    for r in requests:
        # Форматуємо текст кнопки: емодзі статусу + користувач + телефон
        user = f"{r.get('first_name') or ''} {r.get('last_name') or ''}".strip() or "Без імені"
        status = r.get('status', 'new')
        if status == 'cancelled':
            status_emoji = "❌"
        elif status == 'done':
            status_emoji = "🔵"
        else:
            status_emoji = "🟢"
        
        button_text = f"{status_emoji} {user}"
        
        # Додаємо телефон якщо є
        if r.get('phone'):
            button_text += f" • {r.get('phone')}"
        
        # Додаємо інформацію про авто якщо є
        if r.get('vehicle_id_ref'):
            vehicle_info = f"{r.get('vehicle_brand') or ''} {r.get('vehicle_model') or ''}".strip()
            if vehicle_info:
                button_text += f" • 🚛 {vehicle_info}"
        
        # Обмежуємо довжину тексту кнопки
        if len(button_text) > 60:
            button_text = button_text[:57] + "..."
        
        rows.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_request_{r['id']}"
        )])
    
    # Пагінація якщо є більше однієї сторінки (у стилі "Всі авто")
    total_pages = (total + per_page - 1) // per_page if total else 1
    if total_pages > 1:
        pagination_buttons = []
        
        # Кнопка "Попередня"
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton(
                text="⬅️ Попередня",
                callback_data=f"admin_requests:{status_filter}:{sort}:{page-1}"
            ))
        
        # Кнопка з номером поточної сторінки
        pagination_buttons.append(InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data="current_page_info"
        ))
        
        # Кнопка "Наступна"
        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton(
                text="Наступна ➡️",
                callback_data=f"admin_requests:{status_filter}:{sort}:{page+1}"
            ))
        
        rows.append(pagination_buttons)
    
    # Кнопка "Назад"
    rows.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_admin_panel"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_request_detail_keyboard(request: dict, status_filter: str = "all", sort: str = "newest", page: int = 1) -> InlineKeyboardMarkup:
    toggle_text = "🔄 Позначити як Опрацьована" if request.get('status') != 'done' else "🔄 Позначити як Нова"
    rows = []
    # Дії переходу
    if request.get('user_id'):
        rows.append([InlineKeyboardButton(text="👤 Відкрити користувача", callback_data=f"view_user_{request['user_id']}")])
    if request.get('vehicle_id_ref'):
        rows.append([InlineKeyboardButton(text="🚛 Відкрити авто", callback_data=f"view_vehicle_{request['vehicle_id_ref']}")])
    
    # Зміна статусу - тільки якщо заявка не скасована
    if request.get('status') != 'cancelled':
        rows.append([InlineKeyboardButton(text=toggle_text, callback_data=f"toggle_request_status_{request['id']}")])
        rows.append([InlineKeyboardButton(text="❌ Скасувати заявку", callback_data=f"cancel_request_{request['id']}")])
    else:
        # Для скасованих заявок показуємо кнопку відновлення
        rows.append([InlineKeyboardButton(text="♻️ Відновити заявку", callback_data=f"restore_request_{request['id']}")])
    
    # Назад до списку заявок із збереженими фільтрами
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_requests:{status_filter}:{sort}:{page}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


