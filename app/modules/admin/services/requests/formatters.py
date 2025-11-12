from typing import List, Dict


def format_requests_list(requests: List[Dict], status_filter: str = "all", sort: str = "newest", page: int = 1, total: int = 0, per_page: int = 10, stats: Dict | None = None) -> str:
    """Форматувати список заявок у стилі блоку 'Всі авто'"""
    
    # Заголовок зі статусом фільтру
    status_text_map = {
        "all": "Всі заявки",
        "new": "Нові заявки",
        "done": "Опрацьовані заявки"
    }
    status_text = status_text_map.get(status_filter, "Всі заявки")
    
    text = f"📨 <b>{status_text}</b>\n\n"
    
    # Статистика у стилі "Всі авто"
    text += "📊 <b>Статистика:</b>\n"
    if stats:
        text += f"• 📨 <b>Всього заявок:</b> {stats.get('total', 0)}\n"
        text += f"• 🟢 <b>Нових:</b> {stats.get('new', 0)}\n"
        text += f"• 🔵 <b>Опрацьованих:</b> {stats.get('done', 0)}\n"
    else:
        text += f"• 📨 <b>Знайдено заявок:</b> {total}\n"
    
    # Інформація про сортування
    sort_names = {
        "newest": "📅 Дата (нові → старі)",
        "oldest": "📅 Дата (старі → нові)",
        "date_desc": "📅 Дата (нові → старі)",
        "date_asc": "📅 Дата (старі → нові)",
    }
    sort_name = sort_names.get(sort, "📅 Дата (нові → старі)")
    text += f"\n🔄 <b>Сортування:</b> {sort_name}\n"
    
    # Пагінація
    if total:
        total_pages = (total + per_page - 1) // per_page
        text += f"📄 <b>Сторінка {page} з {total_pages}</b>\n"
    
    # Якщо немає заявок
    if not requests:
        text += "\n❌ <b>Заявок не знайдено</b>\nПоки що немає заявок."
        return text
    
    return text


def format_request_detail(r: Dict) -> str:
    """Формат детальної картки заявки у зрозумілому вигляді для адміна."""
    user = f"{r.get('first_name') or ''} {r.get('last_name') or ''}".strip() or "Без імені"

    status_map = {"new": "🟢 Нова", "done": "🔵 Опрацьована"}
    status_text = status_map.get(r.get("status"), r.get("status") or "—")

    type_map = {
        "vehicle_application": "Заявка по авто",
        "buy_vehicle": "Купівля авто",
    }
    type_text = type_map.get(r.get("request_type"), r.get("request_type") or "—")

    # Авто (якщо прив'язане)
    if r.get('vehicle_id_ref'):
        price_val = int(r.get('vehicle_price') or 0)
        price_part = f" • ${price_val:,}" if price_val else ""
        vehicle_line = f"#{r['vehicle_id_ref']} • {r.get('vehicle_brand') or ''} {r.get('vehicle_model') or ''}{price_part}"
    else:
        vehicle_line = "—"

    # Додаємо інформацію про обробку адміністратором
    processed_info = ""
    if r.get("processed_by_admin_id") and r.get("processed_at"):
        from datetime import datetime
        try:
            processed_dt = datetime.fromisoformat(r["processed_at"])
            processed_date = processed_dt.strftime("%d.%m.%Y %H:%M")
            processed_info = f"\n👤 Обробив: Адмін ID {r['processed_by_admin_id']}\n⏰ Час: {processed_date}"
        except Exception:
            processed_info = f"\n👤 Обробив: Адмін ID {r['processed_by_admin_id']}"

    text = (
        "📨 <b>Заявка</b>\n\n"
        f"ID: <b>{r['id']}</b>\n"
        f"Статус: <b>{status_text}</b>\n"
        f"Тип: <b>{type_text}</b>\n"
        f"Користувач: <b>{user}</b> (📞 {r.get('phone') or '—'})\n"
        f"Авто: {vehicle_line}{processed_info}\n\n"
        f"Деталі:\n{r.get('details') or '—'}"
    )

    return text


