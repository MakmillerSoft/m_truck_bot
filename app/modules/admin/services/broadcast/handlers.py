"""
Обробники створення розсилки в групу (адмін)
Ланцюжкове введення: текст → кнопки → медіа → підтвердження → відправка
"""
import logging
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.modules.admin.core.access_control import AdminAccessFilter
from app.utils.formatting import get_default_parse_mode
from app.config.settings import settings
from app.modules.database.manager import db_manager

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast_handlers")
router.message.filter(AdminAccessFilter())
router.callback_query.filter(AdminAccessFilter())

import asyncio
from typing import Dict, List
from datetime import datetime, timedelta

# Тимчасове сховище для медіагруп розсилки з timestamp для автоочищення
_broadcast_media_groups: Dict[str, Dict] = {}
_cleanup_task = None  # Задача для періодичного очищення


def _clean_file_id(file_id: str) -> str:
    """Видаляє префікс video: з file_id якщо він є"""
    if file_id and isinstance(file_id, str) and file_id.startswith("video:"):
        return file_id.replace("video:", "", 1)
    return file_id


async def _cleanup_old_media_groups():
    """Періодичне очищення старих медіагруп (старше 1 години)"""
    while True:
        try:
            await asyncio.sleep(1800)  # Перевірка кожні 30 хвилин
            current_time = datetime.now()
            expired_groups = []
            
            for group_id, entry in _broadcast_media_groups.items():
                created_at = entry.get('created_at')
                if created_at and (current_time - created_at) > timedelta(hours=1):
                    expired_groups.append(group_id)
            
            # Видаляємо застарілі групи
            for group_id in expired_groups:
                del _broadcast_media_groups[group_id]
                logger.warning(f"🧹 Видалено застарілу медіагрупу: {group_id}")
            
            if expired_groups:
                logger.info(f"🧹 Очищено {len(expired_groups)} застарілих медіагруп")
                
        except Exception as e:
            logger.error(f"❌ Помилка очищення медіагруп: {e}")
            await asyncio.sleep(60)  # При помилці чекаємо 1 хвилину


def _start_cleanup_task():
    """Запуск задачі автоочищення"""
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_cleanup_old_media_groups())
        logger.info("✅ Запущено задачу автоочищення медіагруп")


async def _safe_edit_text(callback: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    """Edit text safely; if not possible, send a new message instead."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=get_default_parse_mode())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=get_default_parse_mode())


class BroadcastStates(StatesGroup):
    waiting_for_text = State()
    asking_for_buttons = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()
    asking_for_media = State()
    waiting_for_media = State()
    confirm_send = State()
    waiting_for_topic = State()
    # Налаштування: додавання топіка (послідовно: назва → thread_id)
    settings_waiting_topic_name = State()  # Для додавання нового топіка
    settings_waiting_topic_id = State()
    # Налаштування: редагування топіка
    settings_waiting_rename_topic_name = State()  # Для редагування назви існуючого топіка


# Кеш топіків групи з автоматичним оновленням
TOPICS = {}
_TOPICS_CACHE_TIMESTAMP = None
_TOPICS_CACHE_TTL = 300  # TTL 5 хвилин (300 секунд)


async def load_group_topics(bot, force_refresh: bool = False) -> dict:
    """Завантажити гілки (forum topics) з групи з автоматичним кешуванням.
    
    Args:
        bot: Екземпляр бота (для майбутнього розширення)
        force_refresh: Примусово оновити кеш, ігноруючи TTL
    
    Returns:
        dict: Мапа назва_топіка → thread_id
    """
    global TOPICS, _TOPICS_CACHE_TIMESTAMP
    
    current_time = datetime.now()
    
    # Перевіряємо чи потрібно оновити кеш
    should_refresh = (
        force_refresh or 
        _TOPICS_CACHE_TIMESTAMP is None or 
        (current_time - _TOPICS_CACHE_TIMESTAMP).total_seconds() > _TOPICS_CACHE_TTL
    )
    
    if should_refresh:
        # Завантажуємо топіки з БД
        topics: dict[str, int] = {}
        rows = await db_manager.get_group_topics()
        for row in rows:
            topics[row.name] = row.thread_id
        
        TOPICS = topics
        _TOPICS_CACHE_TIMESTAMP = current_time
        
        if force_refresh:
            logger.info(f"🔄 Кеш топіків примусово оновлено: {len(TOPICS)} топіків")
        else:
            logger.info(f"🔄 Кеш топіків автоматично оновлено: {len(TOPICS)} топіків (TTL: {_TOPICS_CACHE_TTL}с)")
    
    return TOPICS


@router.callback_query(F.data == "admin_broadcast")
async def broadcast_main_menu(callback: CallbackQuery, state: FSMContext):
    """Головне меню розсилки"""
    logger.info(f"🔔 Обробник broadcast_main_menu викликаний для користувача {callback.from_user.id}")
    
    # Запускаємо задачу автоочищення при першому виклику
    _start_cleanup_task()
    
    await callback.answer()
    from app.modules.admin.shared.modules.keyboards.main_keyboards import get_admin_broadcast_keyboard
    await callback.message.edit_text(
        "📢 <b>Розсилка</b>\n\nОберіть дію:",
        reply_markup=get_admin_broadcast_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "admin_broadcast_history")
async def broadcast_history(callback: CallbackQuery, state: FSMContext):
    """Історія розсилок"""
    await callback.answer()
    
    try:
        from .formatters import format_broadcast_list_header
        from .keyboards import get_broadcasts_list_keyboard
        
        # Отримуємо статистику
        stats = await db_manager.get_broadcasts_statistics()
        
        # Отримуємо першу сторінку розсилок з сортуванням за датою
        broadcasts = await db_manager.list_broadcasts(limit=settings.page_size, offset=0, sort_by="created_at_desc", status_filter="all")
        
        # Отримуємо загальну кількість сторінок
        total_broadcasts = stats['total_broadcasts']
        total_pages = (total_broadcasts + settings.page_size - 1) // settings.page_size if total_broadcasts > 0 else 1
        
        # Форматуємо заголовок
        header_text = format_broadcast_list_header(
            total_broadcasts=stats['total_broadcasts'],
            sent_broadcasts=stats['sent_broadcasts'],
            draft_broadcasts=stats['draft_broadcasts'],
            current_page=1,
            total_pages=total_pages,
            status_filter="all"
        )
        
        if not broadcasts:
            header_text += "\n\n❌ <b>Розсилки не знайдені</b>\nПоки що немає створених розсилок."
        
        # Відправляємо повідомлення зі статистикою та списком розсилок
        await callback.message.edit_text(
            header_text,
            reply_markup=get_broadcasts_list_keyboard(broadcasts, current_page=1, total_pages=total_pages, sort_by="created_at_desc", status_filter="all"),
            parse_mode=get_default_parse_mode(),
        )
        
        # Зберігаємо поточну сторінку та сортування в стані
        await state.update_data(broadcasts_page=1, broadcasts_sort="created_at_desc", broadcasts_status_filter="all", total_pages=total_pages)
        
        logger.info(f"📋 Показано історію розсилок для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження історії розсилок: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ <b>Помилка завантаження</b>\n\n{str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_broadcast")]
            ]),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data == "admin_create_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Крок 1: Запит тексту розсилки"""
    await state.clear()
    await state.update_data(text=None, button_text=None, button_url=None, media=None, media_group=None)
    
    await callback.message.edit_text(
        "📢 <b>Створення розсилки</b>\n\n<b>Крок 1 з 5:</b> Введіть текст розсилки\n\n<i>HTML розмітка дозволена</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_broadcast")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.waiting_for_text)


@router.message(BroadcastStates.waiting_for_text, F.text)
async def save_text(message: Message, state: FSMContext):
    """Збереження тексту та перехід до кнопок"""
    await state.update_data(text=message.html_text or message.text)
    
    await message.answer(
        "✅ <b>Текст збережено</b>\n\n<b>Крок 2 з 5:</b> Додати кнопку до розсилки?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Так", callback_data="broadcast_add_button")],
            [InlineKeyboardButton(text="❌ Ні", callback_data="broadcast_skip_button")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_text")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.asking_for_buttons)


@router.callback_query(F.data == "broadcast_back_to_text")
async def back_to_text(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення тексту"""
    await callback.answer()
    await _safe_edit_text(
        callback,
        "📢 <b>Створення розсилки</b>\n\n<b>Крок 1 з 5:</b> Введіть текст розсилки\n\n<i>HTML розмітка дозволена</i>",
        InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_broadcast")]])
    )
    await state.set_state(BroadcastStates.waiting_for_text)


@router.callback_query(F.data == "broadcast_add_button")
async def ask_button_text(callback: CallbackQuery, state: FSMContext):
    """Запит тексту кнопки"""
    await callback.answer()
    await callback.message.edit_text(
        "🔗 <b>Крок 2 з 5:</b> Введіть текст кнопки",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_buttons_question")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.waiting_for_button_text)


@router.callback_query(F.data == "broadcast_skip_button")
async def skip_button(callback: CallbackQuery, state: FSMContext):
    """Пропуск кнопки та перехід до медіа"""
    await callback.answer()
    await _safe_edit_text(
        callback,
        "✅ <b>Кнопку пропущено</b>\n\n<b>Крок 3 з 5:</b> Додати медіа до розсилки?",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Так", callback_data="broadcast_add_media")],
            [InlineKeyboardButton(text="❌ Ні", callback_data="broadcast_skip_media")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_buttons_question")]
        ])
    )
    await state.set_state(BroadcastStates.asking_for_media)


@router.callback_query(F.data == "broadcast_back_to_buttons_question")
async def back_to_buttons_question(callback: CallbackQuery, state: FSMContext):
    """Повернення до питання про кнопки"""
    await callback.answer()
    await _safe_edit_text(
        callback,
        "✅ <b>Текст збережено</b>\n\n<b>Крок 2 з 5:</b> Додати кнопку до розсилки?",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Так", callback_data="broadcast_add_button")],
            [InlineKeyboardButton(text="❌ Ні", callback_data="broadcast_skip_button")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_text")]
        ])
    )
    await state.set_state(BroadcastStates.asking_for_buttons)


@router.message(BroadcastStates.waiting_for_button_text, F.text)
async def save_button_text(message: Message, state: FSMContext):
    """Збереження тексту кнопки та запит URL"""
    await state.update_data(button_text=message.text)
    
    await message.answer(
        f"✅ <b>Текст кнопки збережено:</b> {message.text}\n\n<b>Крок 2.1 з 5:</b> Введіть посилання для кнопки",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_button_text")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.waiting_for_button_url)


@router.callback_query(F.data == "broadcast_back_to_button_text")
async def back_to_button_text(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення тексту кнопки"""
    await callback.answer()
    await _safe_edit_text(
        callback,
        "🔗 <b>Крок 2 з 5:</b> Введіть текст кнопки",
        InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_buttons_question")]])
    )
    await state.set_state(BroadcastStates.waiting_for_button_text)


@router.message(BroadcastStates.waiting_for_button_url, F.text)
async def save_button_url(message: Message, state: FSMContext):
    """Збереження URL кнопки та перехід до медіа"""
    await state.update_data(button_url=message.text)
    
    await message.answer(
        f"✅ <b>Кнопку створено:</b> {message.text}\n\n<b>Крок 3 з 5:</b> Додати медіа до розсилки?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Так", callback_data="broadcast_add_media")],
            [InlineKeyboardButton(text="❌ Ні", callback_data="broadcast_skip_media")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_button_url")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.asking_for_media)


@router.callback_query(F.data == "broadcast_back_to_button_url")
async def back_to_button_url(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення URL кнопки"""
    await callback.answer()
    data = await state.get_data()
    button_text = data.get("button_text", "")
    
    await _safe_edit_text(
        callback,
        f"✅ <b>Текст кнопки збережено:</b> {button_text}\n\n<b>Крок 2.1 з 5:</b> Введіть посилання для кнопки",
        InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_button_text")]])
    )
    await state.set_state(BroadcastStates.waiting_for_button_url)


@router.callback_query(F.data == "broadcast_add_media")
async def ask_media(callback: CallbackQuery, state: FSMContext):
    """Запит медіа"""
    await callback.answer()
    await _safe_edit_text(
        callback,
        "🖼️ <b>Крок 3 з 5:</b> Надішліть фото, відео або медіагрупу",
        InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_media_question")]])
    )
    await state.set_state(BroadcastStates.waiting_for_media)


@router.callback_query(F.data == "broadcast_skip_media")
async def skip_media(callback: CallbackQuery, state: FSMContext):
    """Пропуск медіа та перехід до підтвердження"""
    await callback.answer()
    await show_summary(callback, state)


@router.callback_query(F.data == "broadcast_back_to_media_question")
async def back_to_media_question(callback: CallbackQuery, state: FSMContext):
    """Повернення до питання про медіа"""
    await callback.answer()
    await _safe_edit_text(
        callback,
        "✅ <b>Кнопку створено</b>\n\n<b>Крок 3 з 5:</b> Додати медіа до розсилки?",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Так", callback_data="broadcast_add_media")],
            [InlineKeyboardButton(text="❌ Ні", callback_data="broadcast_skip_media")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_button_url")]
        ])
    )
    await state.set_state(BroadcastStates.asking_for_media)


@router.message(BroadcastStates.waiting_for_media)
async def save_media(message: Message, state: FSMContext):
    """Збереження медіа"""
    # Якщо це медіагрупа – збираємо всі елементи аналогічно створенню авто
    if getattr(message, 'media_group_id', None):
        # Використовуємо комбінацію user_id + media_group_id для унікальності
        # Це запобігає конфлікту між різними адміністраторами
        user_id = message.from_user.id
        media_group_id = message.media_group_id
        group_id = f"{user_id}_{media_group_id}"
        
        entry = _broadcast_media_groups.get(group_id)
        if not entry:
            entry = {
                'items': [],
                'chat_id': message.chat.id,
                'bot': message.bot,
                'state': state,
                'created_at': datetime.now(),  # Додаємо timestamp для автоочищення
                'user_id': user_id,  # Додаємо user_id для логування
                'original_media_group_id': media_group_id,  # Зберігаємо оригінальний ID
            }
            _broadcast_media_groups[group_id] = entry
            # Запускаємо відкладену обробку групи
            asyncio.create_task(_finalize_broadcast_media_group(group_id, 2.0))

        if message.photo:
            file_id = message.photo[-1].file_id
            entry['items'].append({'type': 'photo', 'file_id': file_id})
        elif message.video:
            file_id = message.video.file_id
            entry['items'].append({'type': 'video', 'file_id': file_id})
        else:
            # Пропускаємо не підтримувані типи в групі
            pass
        return

    # Інакше – одиночне медіа
    media_data = None
    if message.photo:
        media_data = {"type": "photo", "file_id": message.photo[-1].file_id}
    elif message.video:
        media_data = {"type": "video", "file_id": message.video.file_id}
    else:
        await message.answer("❌ Підтримуються лише фото, відео або медіагрупи.")
        return

    await state.update_data(media=media_data, media_group=None)
    await show_summary(message, state)


async def _finalize_broadcast_media_group(group_id: str, delay: float):
    """Фіналізація медіагрупи після затримки"""
    await asyncio.sleep(delay)
    entry = _broadcast_media_groups.get(group_id)
    if not entry:
        logger.debug(f"Медіагрупа {group_id} вже оброблена або видалена")
        return
    
    items: List[Dict] = entry['items']
    state: FSMContext = entry['state']
    user_id = entry.get('user_id', 'unknown')
    original_media_group_id = entry.get('original_media_group_id', group_id)
    
    # Зберігаємо у стані як media_group з масивом елементів
    # Використовуємо original_media_group_id для збереження в БД
    await state.update_data(media={"type": "media_group", "items": items, "group_id": original_media_group_id})
    
    # Очищаємо кеш
    try:
        del _broadcast_media_groups[group_id]
        logger.debug(f"✅ Медіагрупа {group_id} (користувач {user_id}) оброблена та видалена")
    except KeyError:
        logger.warning(f"⚠️ Медіагрупа {group_id} вже була видалена")
    # Показуємо підсумок через бота напряму
    bot = entry['bot']
    chat_id = entry['chat_id']
    
    # Отримуємо дані для підсумку
    data = await state.get_data()
    text = data.get("text", "")
    button_text = data.get("button_text")
    button_url = data.get("button_url")
    media = data.get("media")
    
    summary_text = "📢 <b>Підсумок розсилки</b>\n\n"
    summary_text += f"📝 <b>Текст:</b>\n{text}\n\n"
    
    if button_text and button_url:
        summary_text += f"🔗 <b>Кнопка:</b> {button_text} → {button_url}\n\n"
    
    if media:
        if media["type"] == "photo":
            summary_text += "🖼️ <b>Медіа:</b> Фото\n\n"
        elif media["type"] == "video":
            summary_text += "🎥 <b>Медіа:</b> Відео\n\n"
        elif media["type"] == "media_group":
            summary_text += "📸 <b>Медіа:</b> Медіагрупа\n\n"
    
    summary_text += "Оберіть дію:"
    
    keyboard = [
        [InlineKeyboardButton(text="✏️ Редагувати", callback_data="broadcast_edit")],
        [InlineKeyboardButton(text="🚀 Відправити", callback_data="broadcast_send")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_broadcast")],
    ]
    
    # Відправляємо повідомлення через бота
    await bot.send_message(
        chat_id=chat_id,
        text=summary_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode=get_default_parse_mode(),
    )
    # Встановлюємо стан підтвердження
    await state.set_state(BroadcastStates.confirm_send)


async def show_summary(callback_or_message, state: FSMContext):
    """Показ підсумкової картки розсилки"""
    data = await state.get_data()
    text = data.get("text", "")
    button_text = data.get("button_text")
    button_url = data.get("button_url")
    media = data.get("media")
    
    summary_text = "📢 <b>Підсумок розсилки</b>\n\n"
    summary_text += f"📝 <b>Текст:</b>\n{text}\n\n"
    
    if button_text and button_url:
        summary_text += f"🔗 <b>Кнопка:</b> {button_text} → {button_url}\n\n"
    
    if media:
        if media["type"] == "photo":
            summary_text += "🖼️ <b>Медіа:</b> Фото\n\n"
        elif media["type"] == "video":
            summary_text += "🎥 <b>Медіа:</b> Відео\n\n"
        elif media["type"] == "media_group":
            summary_text += "📸 <b>Медіа:</b> Медіагрупа\n\n"
    
    summary_text += "Оберіть дію:"
    
    keyboard = [
        [InlineKeyboardButton(text="✏️ Редагувати", callback_data="broadcast_edit")],
        [InlineKeyboardButton(text="🚀 Відправити", callback_data="broadcast_send")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_broadcast")],
    ]
    
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(
            summary_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode=get_default_parse_mode(),
        )
    else:
        await callback_or_message.answer(
            summary_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode=get_default_parse_mode(),
        )
    
    await state.set_state(BroadcastStates.confirm_send)


@router.callback_query(F.data == "broadcast_edit")
async def edit_broadcast(callback: CallbackQuery, state: FSMContext):
    """Редагування розсилки"""
    await callback.answer()
    await callback.message.edit_text(
        "✏️ <b>Редагування розсилки</b>\n\nЩо хочете змінити?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Текст", callback_data="broadcast_edit_text")],
            [InlineKeyboardButton(text="🔗 Кнопка", callback_data="broadcast_edit_button")],
            [InlineKeyboardButton(text="🖼️ Медіа", callback_data="broadcast_edit_media")],
            [InlineKeyboardButton(text="🔙 Назад до підсумку", callback_data="broadcast_back_to_summary")]
        ]),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "broadcast_edit_text")
async def edit_text(callback: CallbackQuery, state: FSMContext):
    """Редагування тексту"""
    await callback.answer()
    await callback.message.edit_text(
        "📝 <b>Редагування тексту</b>\n\nВведіть новий текст розсилки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_edit")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.waiting_for_text)


@router.callback_query(F.data == "broadcast_edit_button")
async def edit_button(callback: CallbackQuery, state: FSMContext):
    """Редагування кнопки"""
    await callback.answer()
    await callback.message.edit_text(
        "🔗 <b>Редагування кнопки</b>\n\nЩо хочете зробити з кнопкою?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Змінити текст", callback_data="broadcast_edit_button_text")],
            [InlineKeyboardButton(text="🔗 Змінити посилання", callback_data="broadcast_edit_button_url")],
            [InlineKeyboardButton(text="🗑️ Видалити кнопку", callback_data="broadcast_delete_button")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_edit")]
        ]),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "broadcast_edit_button_text")
async def edit_button_text(callback: CallbackQuery, state: FSMContext):
    """Редагування тексту кнопки"""
    await callback.answer()
    await callback.message.edit_text(
        "✏️ <b>Редагування тексту кнопки</b>\n\nВведіть новий текст кнопки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_edit_button")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.waiting_for_button_text)


@router.callback_query(F.data == "broadcast_edit_button_url")
async def edit_button_url(callback: CallbackQuery, state: FSMContext):
    """Редагування URL кнопки"""
    await callback.answer()
    await callback.message.edit_text(
        "🔗 <b>Редагування посилання кнопки</b>\n\nВведіть нове посилання:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_edit_button")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.waiting_for_button_url)


@router.callback_query(F.data == "broadcast_delete_button")
async def delete_button(callback: CallbackQuery, state: FSMContext):
    """Видалення кнопки"""
    await callback.answer()
    await state.update_data(button_text=None, button_url=None)
    await show_summary(callback, state)


@router.callback_query(F.data == "broadcast_edit_media")
async def edit_media(callback: CallbackQuery, state: FSMContext):
    """Редагування медіа"""
    await callback.answer()
    await callback.message.edit_text(
        "🖼️ <b>Редагування медіа</b>\n\nЩо хочете зробити з медіа?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Замінити", callback_data="broadcast_replace_media")],
            [InlineKeyboardButton(text="🗑️ Видалити", callback_data="broadcast_delete_media")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_edit")]
        ]),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "broadcast_replace_media")
async def replace_media(callback: CallbackQuery, state: FSMContext):
    """Заміна медіа"""
    await callback.answer()
    await callback.message.edit_text(
        "🖼️ <b>Заміна медіа</b>\n\nНадішліть нове фото, відео або медіагрупу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_edit_media")]
        ]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.waiting_for_media)


@router.callback_query(F.data == "broadcast_delete_media")
async def delete_media(callback: CallbackQuery, state: FSMContext):
    """Видалення медіа"""
    await callback.answer()
    await state.update_data(media=None)
    await show_summary(callback, state)


@router.callback_query(F.data == "broadcast_back_to_summary")
async def back_to_summary(callback: CallbackQuery, state: FSMContext):
    """Повернення до підсумку"""
    await callback.answer()
    await show_summary(callback, state)


@router.callback_query(F.data == "broadcast_send")
async def send_broadcast(callback: CallbackQuery, state: FSMContext):
    """Відправка розсилки - вибір топика"""
    await callback.answer()
    
    # Підвантажуємо топіки динамічно (якщо можливо)
    global TOPICS
    # Завжди оновлюємо список топіків з БД (щоб уникнути кешу)
    global TOPICS
    TOPICS = await load_group_topics(callback.bot)

    # Створюємо кнопки для топіків
    topic_buttons = []
    # Додаємо дефолтний топік General (без thread_id)
    topic_buttons.append([InlineKeyboardButton(text="🧵 General", callback_data="broadcast_topic_general")])
    for topic_name, thread_id in TOPICS.items():
        topic_buttons.append([InlineKeyboardButton(text=topic_name, callback_data=f"broadcast_topic_{thread_id}")])
    
    if TOPICS:
        topic_buttons.append([InlineKeyboardButton(text="📣 Всі гілки", callback_data="broadcast_topic_all")])
    topic_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_back_to_summary")])
    
    await callback.message.edit_text(
        "🚀 <b>Відправка розсилки</b>\n\nОберіть гілку групи для розсилки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=topic_buttons),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.waiting_for_topic)


@router.callback_query(F.data.startswith("broadcast_topic_"))
async def send_to_topic(callback: CallbackQuery, state: FSMContext):
    """Відправка розсилки в обраний топик"""
    await callback.answer()
    
    topic_part = callback.data.split("_")[2]
    # "all" обробляється окремим обробником send_to_all_topics
    # "general" обробляється тут
    if topic_part == "general":
        # Відправка у головний топік (без thread_id)
        await _send_broadcast_to_chat(callback, state, thread_id=None)
        return
    
    # Інакше - це thread_id конкретного топіка
    thread_id = int(topic_part)
    await _send_broadcast_to_chat(callback, state, thread_id=thread_id)


@router.callback_query(F.data == "broadcast_topic_all")
async def send_to_all_topics(callback: CallbackQuery, state: FSMContext):
    """Відправка розсилки у всі доступні гілки"""
    await callback.answer()
    global TOPICS
    # Завжди підвантажуємо свіжі топіки
    global TOPICS
    TOPICS = await load_group_topics(callback.bot)
    # Надсилаємо також у General (без thread_id)
    data = await state.get_data()
    text = data.get("text", "")
    button_text = data.get("button_text")
    button_url = data.get("button_url")
    media = data.get("media")

    # Зберігаємо розсилку в БД перед відправкою
    await db_manager.create_broadcast({
        "text": text,
        "button_text": button_text,
        "button_url": button_url,
        "media_type": media.get("type") if media else None,
        "media_file_id": media.get("file_id") if media else None,
        "media_group_id": media.get("group_id") if media and media.get("type") == "media_group" else None,
        "status": "sent",
        "target": "all_topics",  # Позначаємо, що це розсилка у всі гілки
    })

    buttons = None
    if button_text and button_url:
        buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=button_text, url=button_url)]])

    if not settings.group_chat_id:
        await callback.answer("❌ Не налаштовано group_chat_id", show_alert=True)
        return
    chat_id = settings.group_chat_id

    # Спочатку General (thread_id = None)
    errors = 0
    general_thread_id = None
    try:
        if media and media.get("type") == "photo":
            await callback.bot.send_photo(chat_id, media.get("file_id"), caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=general_thread_id)
        elif media and media.get("type") == "video":
            video_file_id = _clean_file_id(media.get("file_id"))
            await callback.bot.send_video(chat_id, video_file_id, caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=general_thread_id)
        elif media and media.get("type") == "media_group":
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            media_items = []
            for item in media.get("items", []):
                if item.get("type") == "photo":
                    # Не додаємо caption до медіагрупи - текст буде тільки в повідомленні з кнопкою
                    media_items.append(InputMediaPhoto(media=item.get("file_id")))
                elif item.get("type") == "video":
                    video_file_id = _clean_file_id(item.get("file_id"))
                    # Не додаємо caption до медіагрупи - текст буде тільки в повідомленні з кнопкою
                    media_items.append(InputMediaVideo(media=video_file_id))
            if media_items:
                # Media group не підтримує inline-кнопки в Telegram API
                await callback.bot.send_media_group(chat_id, media=media_items, message_thread_id=general_thread_id)
                # Надішлемо окреме повідомлення з текстом та кнопкою (якщо є текст або кнопка)
                if text or buttons:
                    await callback.bot.send_message(chat_id, text if text else "📢", reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=general_thread_id)
            else:
                await callback.answer("❌ Порожня медіагрупа", show_alert=True)
                return
        else:
            await callback.bot.send_message(chat_id, text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=general_thread_id)
    except Exception as e:
        logger.error(f"Помилка відправки розсилки в General: {e}")
        errors += 1

    # Потім усі гілки з БД
    for topic_id in TOPICS.values():
        try:
            if media and media.get("type") == "photo":
                await callback.bot.send_photo(chat_id, media.get("file_id"), caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=topic_id)
            elif media and media.get("type") == "video":
                video_file_id = _clean_file_id(media.get("file_id"))
                await callback.bot.send_video(chat_id, video_file_id, caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=topic_id)
            elif media and media.get("type") == "media_group":
                from aiogram.types import InputMediaPhoto, InputMediaVideo
                media_items = []
                for item in media.get("items", []):
                    if item.get("type") == "photo":
                        # Не додаємо caption до медіагрупи - текст буде тільки в повідомленні з кнопкою
                        media_items.append(InputMediaPhoto(media=item.get("file_id")))
                    elif item.get("type") == "video":
                        video_file_id = _clean_file_id(item.get("file_id"))
                        # Не додаємо caption до медіагрупи - текст буде тільки в повідомленні з кнопкою
                        media_items.append(InputMediaVideo(media=video_file_id))
                if media_items:
                    # Media group не підтримує inline-кнопки в Telegram API
                    await callback.bot.send_media_group(chat_id, media=media_items, message_thread_id=topic_id)
                    # Надішлемо окреме повідомлення з текстом та кнопкою (якщо є текст або кнопка)
                    if text or buttons:
                        await callback.bot.send_message(chat_id, text if text else "📢", reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=topic_id)
                else:
                    logger.warning(f"Порожня медіагрупа для топіка {topic_id}")
            else:
                await callback.bot.send_message(chat_id, text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=topic_id)
        except Exception as e:
            logger.error(f"Помилка відправки розсилки в топік {topic_id}: {e}")
            errors += 1

    if errors == 0:
        await callback.message.edit_text(
            "✅ <b>Розсилку успішно надіслано у всі гілки!</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад до розсилки", callback_data="admin_broadcast")]]),
            parse_mode=get_default_parse_mode(),
        )
        await state.clear()
    else:
        await callback.answer(f"⚠️ Надіслано з помилками: {errors}", show_alert=True)


async def _send_broadcast_to_chat(callback: CallbackQuery, state: FSMContext, thread_id: int | None):
    data = await state.get_data()
    text = data.get("text", "")
    button_text = data.get("button_text")
    button_url = data.get("button_url")
    media = data.get("media")

    # Визначаємо цільовий топік для збереження в БД
    target_topic = "general" if thread_id is None else f"topic_{thread_id}"

    # Зберігаємо розсилку в історію (чернетку → sent)
    try:
        await db_manager.create_broadcast({
            "text": text,
            "button_text": button_text,
            "button_url": button_url,
            "media_type": media.get("type") if media else None,
            "media_file_id": media.get("file_id") if media else None,
            "media_group_id": media.get("group_id") if media and media.get("type") == "media_group" else None,
            "status": "sent",
        })
        logger.info(f"✅ Розсилка збережена в БД для топіка: {target_topic}")
    except Exception as e:
        logger.error(f"❌ Помилка збереження розсилки в БД: {e}")
        # Продовжуємо відправку навіть якщо збереження не вдалося

    buttons = None
    if button_text and button_url:
        buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=button_text, url=button_url)]])

    if not settings.group_chat_id:
        await callback.answer("❌ Не налаштовано group_chat_id", show_alert=True)
        return

    chat_id = settings.group_chat_id

    try:
        # Відправка: не змінюємо БД і не авто-перейменовуємо топіки
        if media and media.get("type") == "photo":
            await callback.bot.send_photo(chat_id, media.get("file_id"), caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=thread_id)
        elif media and media.get("type") == "video":
            video_file_id = _clean_file_id(media.get("file_id"))
            await callback.bot.send_video(chat_id, video_file_id, caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=thread_id)
        elif media and media.get("type") == "media_group":
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            media_items = []
            for item in media.get("items", []):
                if item.get("type") == "photo":
                    # Не додаємо caption до медіагрупи - текст буде тільки в повідомленні з кнопкою
                    media_items.append(InputMediaPhoto(media=item.get("file_id")))
                elif item.get("type") == "video":
                    video_file_id = _clean_file_id(item.get("file_id"))
                    # Не додаємо caption до медіагрупи - текст буде тільки в повідомленні з кнопкою
                    media_items.append(InputMediaVideo(media=video_file_id))
            if media_items:
                await callback.bot.send_media_group(chat_id, media=media_items, message_thread_id=thread_id)
                # Надішлемо окреме повідомлення з текстом та кнопкою (якщо є текст або кнопка)
                if text or buttons:
                    await callback.bot.send_message(chat_id, text if text else "📢", reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=thread_id)
            else:
                logger.error("Порожня медіагрупа при відправці розсилки")
                await callback.answer("❌ Помилка: порожня медіагрупа", show_alert=True)
                return
        else:
            await callback.bot.send_message(chat_id, text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=thread_id)
    except TelegramBadRequest as e:
        logger.error(f"Помилка розсилки: {e}")
        if "message thread not found" in str(e).lower():
            await callback.answer("❌ Топік не знайдено. Перевірте ID або права бота.", show_alert=True)
        else:
            await callback.answer("❌ Помилка під час відправки повідомлення.", show_alert=True)
        return
    except Exception as e:
        logger.error(f"Помилка розсилки: {e}")
        await callback.answer("❌ Сталася неочікувана помилка під час відправки", show_alert=True)
        return

    await callback.message.edit_text(
        "✅ <b>Розсилку надіслано!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад до розсилки", callback_data="admin_broadcast")]]),
        parse_mode=get_default_parse_mode(),
    )


