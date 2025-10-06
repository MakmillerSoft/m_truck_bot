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
    get_admin_stats_keyboard,
    get_admin_broadcast_keyboard,
    get_admin_settings_keyboard,
    get_admin_reports_keyboard,
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
    # Вхід у верхній рівень адмінки — очищаємо попередні стани
    await state.clear()
    
    main_text = """
🏠 <b>Адмін панель M-Truck</b>

Вітаємо в панелі управління ботом!

<b>Доступні розділи:</b>
• 🚛 <b>Управління авто</b> - додавання, редагування, публікація авто
• 👥 <b>Користувачі</b> - управління користувачами бота
• 📊 <b>Статистика</b> - аналітика та метрики
• 📢 <b>Розсилка</b> - масові повідомлення користувачам
• ⚙️ <b>Налаштування</b> - конфігурація бота
• 📋 <b>Звіти</b> - детальні звіти по роботі

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
• 📝 <b>Чернетки</b> - переглянути незавершені авто

Оберіть дію:
"""
    
    await callback.message.edit_text(
        vehicles_text,
        reply_markup=get_admin_vehicles_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_drafts")
async def admin_drafts_callback(callback: CallbackQuery, state: FSMContext):
    """Чернетки авто"""
    await safe_callback_answer(callback)
    
    drafts_text = """
📝 <b>Чернетки авто</b>

Функція чернеток буде реалізована в наступних версіях.

<i>Тут будуть відображатися незавершені авто, які користувачі почали створювати, але не завершили процес.</i>
"""
    
    # Створюємо клавіатуру з кнопкою "Назад"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад до управління авто",
                    callback_data="admin_vehicles"
                )
            ]
        ]
    )
    
    await callback.message.edit_text(
        drafts_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


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


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery, state: FSMContext):
    """Статистика"""
    await safe_callback_answer(callback)
    await state.clear()
    
    stats_text = """
📊 <b>Статистика</b>

<b>Доступні звіти:</b>
• 📊 <b>Загальна статистика</b> - основні метрики бота
• 🚛 <b>Статистика авто</b> - аналітика по авто
• 👥 <b>Статистика користувачів</b> - метрики користувачів
• 📈 <b>Аналітика</b> - детальна аналітика

Оберіть тип звіту:
"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_stats_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    """Розсилка"""
    await safe_callback_answer(callback)
    await state.clear()
    
    broadcast_text = """
📢 <b>Розсилка</b>

<b>Доступні дії:</b>
• 📢 <b>Створити розсилку</b> - відправити повідомлення всім користувачам
• 📋 <b>Історія розсилок</b> - переглянути попередні розсилки
• ⚙️ <b>Налаштування розсилки</b> - конфігурація розсилки
• 📊 <b>Статистика розсилок</b> - метрики розсилок

Оберіть дію:
"""
    
    await callback.message.edit_text(
        broadcast_text,
        reply_markup=get_admin_broadcast_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_settings")
async def admin_settings_callback(callback: CallbackQuery, state: FSMContext):
    """Налаштування"""
    await safe_callback_answer(callback)
    await state.clear()
    
    settings_text = """
⚙️ <b>Налаштування</b>

<b>Доступні налаштування:</b>
• ⚙️ <b>Загальні налаштування</b> - основні параметри бота
• 🔒 <b>Безпека</b> - налаштування безпеки
• 🤖 <b>Налаштування бота</b> - конфігурація бота
• 📢 <b>Налаштування групи</b> - параметри Telegram групи

Оберіть розділ:
"""
    
    await callback.message.edit_text(
        settings_text,
        reply_markup=get_admin_settings_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_reports")
async def admin_reports_callback(callback: CallbackQuery, state: FSMContext):
    """Звіти"""
    await safe_callback_answer(callback)
    await state.clear()
    
    reports_text = """
📋 <b>Звіти</b>

<b>Доступні звіти:</b>
• 📊 <b>Щоденний звіт</b> - звіт за сьогодні
• 📈 <b>Тижневий звіт</b> - звіт за тиждень
• 📅 <b>Місячний звіт</b> - звіт за місяць
• 📋 <b>Кастомний звіт</b> - звіт за вибраний період

Оберіть тип звіту:
"""
    
    await callback.message.edit_text(
        reports_text,
        reply_markup=get_admin_reports_keyboard(),
        parse_mode="HTML"
    )


# Заглушки для всіх інших callback'ів (крім реалізованих)
@router.callback_query(F.data.startswith("admin_") & ~F.data.in_([
    "admin_all_vehicles", 
    "admin_all_users", 
    "admin_search_users"
]))
async def admin_placeholder_callback(callback: CallbackQuery, state: FSMContext):
    """Заглушка для всіх адмін callback'ів"""
    await safe_callback_answer(callback, "🚧 Функція в розробці")
    
    placeholder_text = """
🚧 <b>Функція в розробці</b>

Ця функція ще не реалізована.
Вона буде доступна в наступних версіях.

🔙 Поверніться до головного меню.
"""
    
    await callback.message.edit_text(
        placeholder_text,
        reply_markup=get_back_to_main_keyboard(),
        parse_mode="HTML"
    )


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
• 📊 <b>Статистика</b> - аналітика та метрики
• 📢 <b>Розсилка</b> - масові повідомлення користувачам
• ⚙️ <b>Налаштування</b> - конфігурація бота
• 📋 <b>Звіти</b> - детальні звіти по роботі

Оберіть розділ для роботи:
"""
    
    await message.answer(
        admin_text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


# Обробник для користувачів без доступу буде в окремому роутері
