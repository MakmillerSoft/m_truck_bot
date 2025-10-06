"""
Форматування результатів пошуку користувачів для адмін панелі
"""
from typing import List
from app.modules.database.models import UserModel


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
        
        role_emoji = "🛒" if user.role == "buyer" else "👑"
        status_emoji = "✅" if user.is_active else "🚫"
        
        text += f"{i}. 👤 <b>{name}</b> {role_emoji} {status_emoji}\n"
        text += f"   ID: {user.id} | Telegram: {user.telegram_id}\n"
        
        if user.username:
            text += f"   Username: @{user.username}\n"
        
        text += "\n"
    
    return text


def format_search_instructions(search_type: str) -> str:
    """
    Форматувати інструкції для пошуку
    
    Args:
        search_type: Тип пошуку
        
    Returns:
        str: Форматовані інструкції
    """
    instructions = {
        "id": "🆔 <b>Пошук по ID користувача</b>\n\nВведіть ID користувача для точного пошуку:",
        "telegram_id": "📱 <b>Пошук по Telegram ID</b>\n\nВведіть Telegram ID користувача:",
        "name": "👤 <b>Пошук по імені</b>\n\nВведіть ім'я, прізвище або username користувача:",
        "phone": "📞 <b>Пошук по телефону</b>\n\nВведіть номер телефону користувача:",
        "role": "🏷️ <b>Пошук по ролі</b>\n\nОберіть роль для пошуку:",
        "verification": "✅ <b>Пошук по верифікації</b>\n\nОберіть статус верифікації:"
    }
    
    return instructions.get(search_type, "Введіть пошуковий термін:")


def format_role_search_results(users: List[UserModel], role: str) -> str:
    """
    Форматувати результати пошуку по ролі
    
    Args:
        users: Список знайдених користувачів
        role: Роль користувачів
        
    Returns:
        str: Форматований текст результатів
    """
    role_names = {
        "buyer": "Покупці",
        "admin": "Адміністратори"
    }
    
    role_emojis = {
        "buyer": "🛒",
        "admin": "👑"
    }
    
    role_name = role_names.get(role, role)
    role_emoji = role_emojis.get(role, "👤")
    
    if not users:
        return f"❌ <b>{role_emoji} {role_name} не знайдені</b>"
    
    text = f"🔍 <b>Результати пошуку: {role_emoji} {role_name}</b>\n\n"
    text += f"📊 <b>Знайдено:</b> {len(users)} користувачів\n\n"
    
    # Список користувачів
    for i, user in enumerate(users, 1):
        name = user.first_name or "Без імені"
        if user.last_name:
            name += f" {user.last_name}"
        
        status_emoji = "✅" if user.is_active else "🚫"
        
        text += f"{i}. 👤 <b>{name}</b> {status_emoji}\n"
        text += f"   ID: {user.id} | Telegram: {user.telegram_id}\n"
        
        if user.username:
            text += f"   Username: @{user.username}\n"
        
        text += "\n"
    
    return text
