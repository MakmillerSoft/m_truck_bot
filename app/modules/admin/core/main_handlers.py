"""
Головні обробники адмін панелі
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from .access_control import AdminAccessFilter
from ..shared.modules.keyboards.main_keyboards import (
    get_admin_main_keyboard,
    get_admin_vehicles_keyboard,
    get_admin_users_keyboard,
    get_admin_broadcast_keyboard,
    get_back_to_main_keyboard
)
from ..shared.utils.callback_utils import safe_callback_answer
from app.modules.client.services.authentication.registration.keyboards import (
    get_main_menu_inline_keyboard,
)
from app.utils.formatting import get_default_parse_mode

logger = logging.getLogger(__name__)
router = Router()


# Застосовуємо фільтр доступу до всіх обробників
router.message.filter(AdminAccessFilter())
router.callback_query.filter(AdminAccessFilter())


@router.callback_query(F.data == "admin_main")
async def admin_main_callback(callback: CallbackQuery, state: FSMContext):
    """Головне меню адмін панелі"""
    await safe_callback_answer(callback)
    
    # Додаткова перевірка доступу (на випадок зміни ролі під час сесії)
    from ..shared.utils.access_utils import require_admin_access
    if not await require_admin_access(callback):
        return
    
    # Вхід у верхній рівень адмінки — очищаємо попередні стани
    await state.clear()
    
    main_text = """
🏠 <b>Адмін панель M-Truck</b>

Вітаємо в панелі управління ботом!

<b>Доступні розділи:</b>
• 🚛 <b>Управління авто</b> - додавання, редагування, публікація авто
• 👥 <b>Користувачі</b> - управління користувачами бота
• 📢 <b>Розсилка</b> - масові повідомлення користувачам
• 📨 <b>Заявки</b> - перегляд та обробка заявок
• 📤 <b>Експорт даних</b> - вивантаження даних в Excel

Оберіть розділ для роботи:
"""
    
    await callback.message.edit_text(
        main_text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_vehicles")
async def admin_vehicles_callback(callback: CallbackQuery, state: FSMContext):
    """Управління авто"""
    await safe_callback_answer(callback)
    # Верхній рівень розділу — очистити попередні стани (не ліземо в ланцюжок створення авто)
    await state.clear()
    
    vehicles_text = """
🚛 <b>Управління авто</b>

<b>Доступні дії:</b>
• ➕ <b>Додати авто</b> - створити нове оголошення
• 📋 <b>Всі авто</b> - переглянути всі авто
• 🔍 <b>Швидкий пошук</b> - знайти авто за критеріями

Оберіть дію:
"""
    
    await callback.message.edit_text(
        vehicles_text,
        reply_markup=get_admin_vehicles_keyboard(),
        parse_mode="HTML"
    )


# admin_drafts - функціонал чернеток видалено (не реалізовано)


@router.callback_query(F.data == "admin_quick_search")
async def admin_quick_search_callback(callback: CallbackQuery, state: FSMContext):
    """Швидкий пошук авто"""
    await safe_callback_answer(callback)
    
    # Перенаправляємо до модуля швидкого пошуку
    from ..services.vehicle_management.quick_search.handlers import show_quick_search_menu
    await show_quick_search_menu(callback)


@router.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery, state: FSMContext):
    """Управління користувачами"""
    await safe_callback_answer(callback)
    # Вхід у розділ користувачів — очистити попередні стани
    await state.clear()
    
    users_text = """
👥 <b>Управління користувачами</b>

<b>Доступні дії:</b>
• 👥 <b>Всі користувачі</b> - переглянути всіх користувачів з пагінацією та фільтрами
• 🔍 <b>Пошук користувачів</b> - знайти користувачів за різними параметрами

Оберіть дію:
"""
    
    await callback.message.edit_text(
        users_text,
        reply_markup=get_admin_users_keyboard(),
        parse_mode="HTML"
    )


# admin_broadcast обробляється в app/modules/admin/services/broadcast/handlers.py


# admin_reports - функціонал звітів видалено (не реалізовано)


# Заглушка видалена - всі основні функції реалізовані
# Якщо потрібна заглушка для нових функцій, додайте їх окремо


@router.callback_query(F.data == "back_to_bot")
async def back_to_bot_callback(callback: CallbackQuery, state: FSMContext):
    """Повернутися до бота"""
    await safe_callback_answer(callback)
    await state.clear()
    # Показуємо головне клієнтське меню у новому повідомленні
    await callback.message.answer(
        "🏠 Головне меню:",
        reply_markup=get_main_menu_inline_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


# Обробник команди /admin для адміністраторів (з фільтром доступу)
@router.message(Command("admin"))
async def admin_command(message: Message):
    """Команда /admin для доступу до адмін панелі"""
    
    admin_text = """
🏠 <b>Адмін панель M-Truck</b>

Вітаємо в панелі управління ботом!

<b>Доступні розділи:</b>
• 🚛 <b>Управління авто</b> - додавання, редагування, публікація авто
• 👥 <b>Користувачі</b> - управління користувачами бота
• 📢 <b>Розсилка</b> - масові повідомлення користувачам
• 📨 <b>Заявки</b> - перегляд та обробка заявок
• 📤 <b>Експорт даних</b> - вивантаження даних в Excel

Оберіть розділ для роботи:
"""
    
    await message.answer(
        admin_text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


# Обробник для користувачів без доступу буде в окремому роутері
