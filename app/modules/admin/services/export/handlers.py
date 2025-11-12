"""
Обробники експорту даних (адмін)
"""
import logging
import os
import aiosqlite
from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError

from app.modules.admin.core.access_control import AdminAccessFilter
from app.utils.formatting import get_default_parse_mode
from .keyboards import get_export_main_keyboard, get_export_back_keyboard
from .excel_generator import generate_excel_export, ExcelExporter

logger = logging.getLogger(__name__)
router = Router(name="admin_export_handlers")
router.message.filter(AdminAccessFilter())
router.callback_query.filter(AdminAccessFilter())


def _get_user_friendly_error(error: Exception) -> str:
    """Отримати зрозуміле повідомлення про помилку для користувача"""
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Database помилки
    if isinstance(error, aiosqlite.Error):
        return "❌ Помилка бази даних. Спробуйте пізніше або зверніться до адміністратора."
    
    # Файлові помилки
    elif isinstance(error, (IOError, OSError)):
        if "No space left" in error_msg or "Disk full" in error_msg:
            return "❌ Недостатньо місця на диску. Зверніться до адміністратора."
        elif "Permission denied" in error_msg:
            return "❌ Помилка доступу до файлу. Зверніться до адміністратора."
        else:
            return "❌ Помилка файлової системи. Спробуйте пізніше."
    
    # Telegram API помилки
    elif isinstance(error, TelegramBadRequest):
        if "file is too big" in error_msg.lower() or "too large" in error_msg.lower():
            return "❌ Файл експорту занадто великий (>50MB). Спробуйте експортувати окремі розділи."
        elif "wrong file identifier" in error_msg.lower():
            return "❌ Помилка завантаження файлу. Спробуйте ще раз."
        else:
            return f"❌ Помилка Telegram API: {error_msg}"
    
    elif isinstance(error, TelegramNetworkError):
        return "❌ Помилка з'єднання з Telegram. Перевірте інтернет та спробуйте пізніше."
    
    # Excel помилки
    elif "openpyxl" in error_type.lower() or "xlsx" in error_msg.lower():
        return "❌ Помилка генерації Excel файлу. Перевірте дані та спробуйте ще раз."
    
    # Невідома помилка
    else:
        logger.error(f"Невідомий тип помилки експорту: {error_type}: {error_msg}")
        return f"❌ Несподівана помилка: {error_type}\n\nЗверніться до адміністратора."


async def _cleanup_export_file(filename: str) -> None:
    """Безпечно видалити тимчасовий файл експорту"""
    try:
        if filename and os.path.exists(filename):
            os.remove(filename)
            logger.debug(f"🗑️ Видалено тимчасовий файл: {filename}")
    except Exception as e:
        logger.warning(f"⚠️ Не вдалося видалити тимчасовий файл {filename}: {e}")


async def _export_data_base(
    callback: CallbackQuery, 
    data_type: str, 
    caption: str, 
    export_method: str
) -> None:
    """Базова функція експорту даних для DRY (Don't Repeat Yourself)
    
    Args:
        callback: CallbackQuery від користувача
        data_type: Тип даних для логування ("користувачів", "авто", "заявок", тощо)
        caption: Опис файлу для користувача
        export_method: Назва методу в ExcelExporter ("export_users", "export_vehicles", тощо)
    """
    await callback.answer()
    filename = None
    
    try:
        # Відправляємо повідомлення про початок експорту
        await callback.message.edit_text(
            f"<b>Експорт {data_type}</b>\n\n⏳ Генерую Excel файл...",
            parse_mode=get_default_parse_mode()
        )
        
        # Генеруємо унікальне ім'я файлу
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{export_method}_{timestamp}.xlsx"
        
        # Створюємо експортер та викликаємо потрібний метод
        exporter = ExcelExporter()
        export_func = getattr(exporter, export_method)
        await export_func()
        await exporter.save(filename)
        
        # Відправляємо файл користувачу
        document = FSInputFile(filename)
        await callback.message.answer_document(
            document=document,
            caption=f"📊 {caption}",
            reply_markup=get_export_back_keyboard()
        )
        
        logger.info(f"✅ Користувач {callback.from_user.id} успішно експортував {data_type}")
        
    except Exception as e:
        # Детальне логування помилки
        logger.error(f"❌ Помилка експорту {data_type}: {type(e).__name__}: {e}", exc_info=True)
        
        # Отримуємо зрозуміле повідомлення для користувача
        user_message = _get_user_friendly_error(e)
        
        # Намагаємося відредагувати або відправити нове повідомлення
        try:
            await callback.message.edit_text(
                f"<b>Експорт {data_type}</b>\n\n{user_message}",
                reply_markup=get_export_back_keyboard(),
                parse_mode=get_default_parse_mode()
            )
        except TelegramBadRequest:
            await callback.message.answer(
                f"<b>Експорт {data_type}</b>\n\n{user_message}",
                reply_markup=get_export_back_keyboard(),
                parse_mode=get_default_parse_mode()
            )
    
    finally:
        # Завжди видаляємо тимчасовий файл
        await _cleanup_export_file(filename)


@router.callback_query(F.data == "admin_export")
async def export_main_menu(callback: CallbackQuery, state: FSMContext):
    """Головне меню експорту"""
    await callback.answer()
    await state.clear()
    
    text = """
📤 <b>Експорт даних</b>

Оберіть які дані ви хочете експортувати в Excel:

• 👥 <b>Користувачі</b> - всі користувачі бота
• 🚛 <b>Авто</b> - всі транспортні засоби
• 📨 <b>Заявки</b> - всі заявки користувачів
• 📢 <b>Розсилки</b> - історія розсилок
• 📦 <b>Всі дані</b> - повний експорт (всі таблиці)

Дані будуть експортовані в Excel файл (.xlsx)
"""
    
    # Перевіряємо чи можемо відредагувати повідомлення (чи є в ньому текст)
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_export_main_keyboard(),
            parse_mode=get_default_parse_mode()
        )
    except:
        # Якщо не можемо відредагувати (наприклад, це документ), відправляємо нове
        await callback.message.answer(
            text,
            reply_markup=get_export_main_keyboard(),
            parse_mode=get_default_parse_mode()
        )


@router.callback_query(F.data == "export_users")
async def export_users(callback: CallbackQuery, state: FSMContext):
    """Експорт користувачів"""
    await _export_data_base(callback, "користувачів", "Експорт користувачів завершено", "export_users")


@router.callback_query(F.data == "export_vehicles")
async def export_vehicles(callback: CallbackQuery, state: FSMContext):
    """Експорт авто"""
    await _export_data_base(callback, "авто", "Експорт авто завершено", "export_vehicles")


@router.callback_query(F.data == "export_requests")
async def export_requests(callback: CallbackQuery, state: FSMContext):
    """Експорт заявок"""
    await _export_data_base(callback, "заявок", "Експорт заявок завершено", "export_requests")


@router.callback_query(F.data == "export_broadcasts")
async def export_broadcasts(callback: CallbackQuery, state: FSMContext):
    """Експорт розсилок"""
    await _export_data_base(callback, "розсилок", "Експорт розсилок завершено", "export_broadcasts")


@router.callback_query(F.data == "export_all")
async def export_all(callback: CallbackQuery, state: FSMContext):
    """Експорт усіх даних"""
    await _export_data_base(callback, "всіх даних", "Повний експорт завершено. Файл містить: користувачів, авто, заявки та розсилки", "export_all")

