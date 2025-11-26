"""
Форматування карток розсилок для адмін панелі
"""
from typing import Optional, Tuple
from app.modules.database.models import BroadcastModel
from datetime import datetime


def format_broadcast_list_header(
    total_broadcasts: int,
    sent_broadcasts: int = 0,
    draft_broadcasts: int = 0,
    current_page: int = 1,
    total_pages: int = 1,
    status_filter: str = "all"
) -> str:
    """
    Форматувати заголовок списку розсилок
    
    Args:
        total_broadcasts: Загальна кількість розсилок
        sent_broadcasts: Кількість відправлених розсилок
        draft_broadcasts: Кількість чернеток
        current_page: Поточна сторінка
        total_pages: Загальна кількість сторінок
        status_filter: Поточний фільтр статусу
        
    Returns:
        str: Форматований заголовок
    """
    # Визначаємо заголовок залежно від фільтра
    if status_filter == "all":
        header_text = "📋 <b>Історія розсилок</b>"
    elif status_filter == "sent":
        header_text = "✅ <b>Відправлені розсилки</b>"
    else:  # draft
        header_text = "📝 <b>Чернетки розсилок</b>"
    
    text = f"{header_text}\n\n"
    
    # Статистика
    text += "📊 <b>Статистика:</b>\n"
    text += f"• 📢 <b>Всього розсилок:</b> {total_broadcasts}\n"
    if status_filter == "all":
        text += f"• ✅ <b>Відправлено:</b> {sent_broadcasts}\n"
        text += f"• 📝 <b>Чернетки:</b> {draft_broadcasts}\n"
    text += "\n"
    
    # Пагінація
    text += f"📄 <b>Сторінка {current_page} з {total_pages}</b>"
    
    return text


def format_broadcast_card(broadcast: BroadcastModel) -> str:
    """
    Форматувати картку розсилки для детального перегляду
    
    Args:
        broadcast: Об'єкт BroadcastModel
        
    Returns:
        str: Форматований текст картки
    """
    text = "📢 <b>Розсилка</b>\n\n"
    
    # Основна інформація
    main_info = []
    
    # ID розсилки
    main_info.append(f"• <b>ID:</b> {broadcast.id}")
    
    # Статус
    status_emoji = "✅" if broadcast.status == "sent" else "📝" if broadcast.status == "draft" else "⏰"
    status_text = "Відправлено" if broadcast.status == "sent" else "Чернетка" if broadcast.status == "draft" else "Заплановано"
    main_info.append(f"• <b>Статус:</b> {status_emoji} {status_text}")
    
    # Дата створення
    if broadcast.created_at:
        created_date = broadcast.created_at.strftime("%d.%m.%Y %H:%M")
        main_info.append(f"• <b>Дата створення:</b> {created_date}")
    
    text += "📋 <b>Основна інформація:</b>\n"
    text += "\n".join(main_info) + "\n\n"
    
    # Текст розсилки
    if broadcast.text:
        text += "📝 <b>Текст:</b>\n"
        # Обмежуємо довжину тексту для перегляду
        display_text = broadcast.text[:300] + "..." if len(broadcast.text) > 300 else broadcast.text
        text += f"{display_text}\n\n"
    
    # Кнопка
    if broadcast.button_text and broadcast.button_url:
        text += "🔗 <b>Кнопка:</b>\n"
        text += f"• <b>Текст:</b> {broadcast.button_text}\n"
        text += f"• <b>URL:</b> {broadcast.button_url}\n\n"
    
    # Медіа
    if broadcast.media_type:
        media_emoji = "🖼️" if broadcast.media_type == "photo" else "🎥" if broadcast.media_type == "video" else "📸"
        media_text = "Фото" if broadcast.media_type == "photo" else "Відео" if broadcast.media_type == "video" else "Медіагрупа"
        text += f"{media_emoji} <b>Медіа:</b> {media_text}\n"
        if broadcast.media_file_id:
            text += f"• <b>File ID:</b> <code>{broadcast.media_file_id[:50]}...</code>\n"
        if broadcast.media_group_id:
            text += f"• <b>Group ID:</b> <code>{broadcast.media_group_id}</code>\n"
        text += "\n"
    
    # Запланована розсилка
    if broadcast.status == "scheduled" and broadcast.scheduled_at:
        scheduled_date = broadcast.scheduled_at.strftime("%d.%m.%Y %H:%M")
        text += f"⏰ <b>Заплановано на:</b> {scheduled_date}\n"
        if broadcast.schedule_period and broadcast.schedule_period != "none":
            period_text = "Щоденно" if broadcast.schedule_period == "daily" else "Щотижня"
            text += f"• <b>Періодичність:</b> {period_text}\n"
        text += "\n"
    
    return text


def format_broadcast_list_item(broadcast: BroadcastModel) -> str:
    """
    Форматувати елемент списку розсилок для кнопки
    
    Args:
        broadcast: Об'єкт BroadcastModel
        
    Returns:
        str: Текст для кнопки
    """
    # Базовий текст з датою
    if broadcast.created_at:
        date_str = broadcast.created_at.strftime("%d.%m.%Y %H:%M")
    else:
        date_str = "Без дати"
    
    # Статус
    status_emoji = "✅" if broadcast.status == "sent" else "📝" if broadcast.status == "draft" else "⏰"
    
    # Медіа
    media_emoji = ""
    if broadcast.media_type:
        media_emoji = "🖼️" if broadcast.media_type == "photo" else "🎥" if broadcast.media_type == "video" else "📸"
    
    # Формуємо текст
    text = f"{status_emoji} {date_str}"
    if media_emoji:
        text += f" {media_emoji}"
    
    # Обмежуємо довжину
    if len(text) > 50:
        text = text[:47] + "..."
    
    return text






