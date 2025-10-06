"""
Форматування карток користувачів для адмін панелі
"""
from typing import Optional, Tuple, List
from app.modules.database.models import UserModel
from datetime import datetime


def format_admin_user_card(user: UserModel, *, admin_is_owner: bool = False, is_self: bool = False) -> Tuple[str, Optional[str]]:
    """
    Форматувати картку користувача для адмін панелі
    
    Args:
        user: Об'єкт UserModel
        
    Returns:
        tuple: (text, photo_file_id) - текст картки та file_id фото (завжди None для користувачів)
    """
    # Заголовок
    name = user.first_name or "Без імені"
    if user.last_name:
        name += f" {user.last_name}"
    
    text = f"👤 <b>{name}</b>\n\n"
    
    # Основна інформація
    main_info = []
    
    # ID користувача
    main_info.append(f"• <b>ID:</b> {user.id}")
    
    # Telegram ID
    main_info.append(f"• <b>Telegram ID:</b> {user.telegram_id}")
    
    # Username
    if user.username:
        main_info.append(f"• <b>Username:</b> @{user.username}")
    
    # Телефон
    if user.phone:
        main_info.append(f"• <b>Телефон:</b> {user.phone}")
    
    # Роль
    role_emoji = "🛒" if user.role == "buyer" else "👑"
    role_text = "Покупець" if user.role == "buyer" else "Адміністратор"
    main_info.append(f"• <b>Роль:</b> {role_emoji} {role_text}")
    
    # Статус активності
    status_emoji = "✅" if user.is_active else "🚫"
    status_text = "Активний" if user.is_active else "Заблокований"
    main_info.append(f"• <b>Статус:</b> {status_emoji} {status_text}")
    
    # Додаємо основну інформацію
    text += "📋 <b>Основна інформація:</b>\n"
    text += "\n".join(main_info) + "\n\n"
    
    # Додаткова інформація
    additional_info = []
    
    # Дата реєстрації
    if user.created_at:
        created_date = user.created_at.strftime("%d.%m.%Y %H:%M")
        additional_info.append(f"• <b>Дата реєстрації:</b> {created_date}")
    
    # Дата останнього оновлення
    if user.updated_at:
        updated_date = user.updated_at.strftime("%d.%m.%Y %H:%M")
        additional_info.append(f"• <b>Останнє оновлення:</b> {updated_date}")
    
    # Додаємо додаткову інформацію
    if additional_info:
        text += "📅 <b>Додаткова інформація:</b>\n"
        text += "\n".join(additional_info) + "\n\n"
    
    # Блок дій / попереджень
    if user.role == "admin" and not admin_is_owner:
        text += "⚠️ <b>Обмеження:</b>\n"
        text += "• Ви не можете редагувати права доступу адміністраторів.\n"
        text += "• Зверніться до власника бота.\n"
    elif is_self:
        text += "⚠️ <b>Обмеження:</b>\n"
        text += "• Ви не можете редагувати власні права доступу чи видалити себе.\n"
        text += "• Зверніться до власника бота.\n"
    else:
        text += "🔧 <b>Дії:</b>\n"
        text += "• Переглянути детальну інформацію\n"
        text += "• Змінити статус активності\n"
        text += "• Видалити користувача\n"
    
    return text, None


def format_users_list_header(
    total_users: int,
    active_users: int,
    blocked_users: int,
    verified_users: int = 0,  # Видалено верифікацію, параметр залишено для сумісності
    current_page: int = 1,
    total_pages: int = 1,
    status_filter: str = "all"
) -> str:
    """
    Форматувати заголовок списку користувачів
    
    Args:
        total_users: Загальна кількість користувачів
        active_users: Кількість активних користувачів
        blocked_users: Кількість заблокованих користувачів
        verified_users: Кількість верифікованих користувачів (не використовується)
        current_page: Поточна сторінка
        total_pages: Загальна кількість сторінок
        status_filter: Поточний фільтр статусу
        
    Returns:
        str: Форматований заголовок
    """
    # Визначаємо заголовок залежно від фільтра
    if status_filter == "all":
        header_text = "👥 <b>Всі користувачі</b>"
    elif status_filter == "active":
        header_text = "✅ <b>Активні користувачі</b>"
    else:  # blocked
        header_text = "🚫 <b>Заблоковані користувачі</b>"
    
    text = f"{header_text}\n\n"
    
    # Статистика
    text += "📊 <b>Статистика:</b>\n"
    text += f"• 👥 <b>Всього користувачів:</b> {total_users}\n"
    text += f"• ✅ <b>Активних:</b> {active_users}\n"
    text += f"• 🚫 <b>Заблокованих:</b> {blocked_users}\n\n"
    
    # Пагінація
    text += f"📄 <b>Сторінка {current_page} з {total_pages}</b>"
    
    return text


def format_user_search_results(users: List[UserModel], search_type: str, search_term: str) -> str:
    """
    Форматувати результати пошуку користувачів
    
    Args:
        users: Список знайдених користувачів
        search_type: Тип пошуку
        search_term: Пошуковий термін
        
    Returns:
        str: Форматований текст результатів
    """
    if not users:
        return f"❌ <b>Користувачі не знайдені</b>\n\nПошук: <b>{search_type}</b> - <code>{search_term}</code>"
    
    # Заголовок
    text = f"🔍 <b>Результати пошуку</b>\n\n"
    text += f"📋 <b>Пошук:</b> {search_type} - <code>{search_term}</code>\n"
    text += f"📊 <b>Знайдено:</b> {len(users)} користувачів\n\n"
    
    # Список користувачів
    for i, user in enumerate(users, 1):
        name = user.first_name or "Без імені"
        if user.last_name:
            name += f" {user.last_name}"
        
        role_emoji = "🛒" if user.role == "buyer" else "🏪" if user.role == "seller" else "👑"
        status_emoji = "✅" if user.is_active else "🚫"
        
        text += f"{i}. 👤 <b>{name}</b> {role_emoji} {status_emoji}\n"
        text += f"   ID: {user.id} | Telegram: {user.telegram_id}\n"
        
        if user.username:
            text += f"   Username: @{user.username}\n"
        
        text += "\n"
    
    return text


def format_user_statistics(stats: dict) -> str:
    """
    Форматувати статистику користувачів
    
    Args:
        stats: Словник зі статистикою
        
    Returns:
        str: Форматована статистика
    """
    text = "📊 <b>Статистика користувачів</b>\n\n"
    
    # Загальна статистика
    text += "👥 <b>Загальна статистика:</b>\n"
    text += f"• <b>Всього користувачів:</b> {stats.get('total_users', 0)}\n"
    text += f"• <b>Активних:</b> {stats.get('active_users', 0)}\n"
    text += f"• <b>Заблокованих:</b> {stats.get('blocked_users', 0)}\n\n"
    
    # Розподіл по ролях
    users_by_role = stats.get('users_by_role', {})
    if users_by_role:
        text += "🏷️ <b>Розподіл по ролях:</b>\n"
        for role, count in users_by_role.items():
            role_emoji = "🛒" if role == "buyer" else "🏪" if role == "seller" else "👑"
            role_text = "Покупці" if role == "buyer" else "Продавці" if role == "seller" else "Адміністратори"
            text += f"• {role_emoji} <b>{role_text}:</b> {count}\n"
    
    return text
