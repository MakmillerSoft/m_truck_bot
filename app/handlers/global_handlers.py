"""
Глобальні обробники команд
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode


router = Router()


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    """Скасувати поточну операцію"""
    current_state = await state.get_state()

    if current_state:
        await state.clear()
        await message.answer(
            "❌ <b>Операцію скасовано</b>\n\n"
            "Ви можете почати заново або використати головне меню",
            parse_mode=get_default_parse_mode(),
        )
    else:
        await message.answer(
            "Немає активних операцій для скасування",
            parse_mode=get_default_parse_mode(),
        )


@router.message(Command("help"))
async def help_command(message: Message):
    """Довідка по командах"""
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)

    if not user:
        help_text = """
🆘 <b>Довідка M-Truck Bot</b>

📝 <b>Доступні команди:</b>
/start - Почати роботу та реєстрацію
/help - Показати цю довідку

👋 Для роботи з ботом спочатку потрібно зареєструватися!
"""
    else:
        help_text = f"""
🆘 <b>Довідка M-Truck Bot</b>

👤 <b>Ваша роль:</b> {user.role}

📝 <b>Основні команди:</b>
/start - Головне меню
/profile - Ваш профіль
/cancel - Скасувати поточну операцію
/help - Показати цю довідку

"""

        if user.role == "admin":
            help_text += """
👨‍💼 <b>Для адміністраторів:</b>
👥 Користувачі - управління покупцями
🚛 Авто - додавання та управління авто
📊 Статистика - аналітика системи
📢 Розсилка - масові повідомлення
📋 Звіти - бізнес звіти

"""
        else:
            # Всі користувачі тепер покупці
            help_text += """
🛒 <b>Ваші можливості:</b>
🔍 Пошук авто - знайти авто за критеріями  
📋 Мої збережені - переглянути збережені авто
🏢 Про компанію - інформація та соцмережі
📞 Контакти - адреси та телефони
💬 Повідомлення - зв'язок з менеджерами

"""

        help_text += f"""
🆘 <b>Підтримка:</b>
📞 Телефон: +380 66 372 69 41
"""

    await message.answer(help_text.strip(), parse_mode=get_default_parse_mode())


@router.message(Command("debug"))
async def debug_command(message: Message, state: FSMContext):
    """Команда для відлагодження (тільки для адмінів)"""
    from app.config.settings import settings

    if message.from_user.id not in settings.get_admin_ids():
        await message.answer(
            "❌ <b>Недостатньо прав</b>", parse_mode=get_default_parse_mode()
        )
        return

    current_state = await state.get_state()
    state_data = await state.get_data()

    debug_info = f"""
🔧 <b>Debug Info</b>

<b>User ID:</b> {message.from_user.id}
<b>Username:</b> @{message.from_user.username or 'None'}
<b>Current State:</b> {current_state or 'None'}
<b>State Data:</b> {state_data}
"""

    await message.answer(debug_info.strip(), parse_mode=get_default_parse_mode())


# ВИМКНЕНО - старий модуль профілю видалено, використовується новий
# @router.message(Command("profile"), StateFilter(None))
# async def profile_command(message: Message):
#     """Показати профіль користувача"""
#     from app.modules.profile.handlers import profile_command as profile_handler
#     await profile_handler(message)


# ВИМКНЕНО - старий модуль профілю видалено
# @router.callback_query(F.data == "back_to_profile")
# async def back_to_profile(callback: CallbackQuery):
#     """Повернутися до профілю"""
#     await callback.answer()
#     user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
#     if not user:
#         await callback.message.edit_text(
#             "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
#             parse_mode=get_default_parse_mode(),
#         )
#         return
#     from app.modules.profile.handlers import show_profile_for_callback
#     await show_profile_for_callback(callback)


# ВИМКНЕНО - старий модуль search видалено
# @router.callback_query(F.data == "show_saved_vehicles_inline")
# async def show_saved_vehicles_inline(callback: CallbackQuery):
#     """Показати збережені авто через inline кнопку"""
#     await callback.answer()
#     from app.modules.search.handlers import show_saved_vehicles_for_callback
#     await show_saved_vehicles_for_callback(callback)
