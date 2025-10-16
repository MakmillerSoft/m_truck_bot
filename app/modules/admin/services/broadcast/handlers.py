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

# Тимчасове сховище для медіагруп розсилки
_broadcast_media_groups: Dict[str, Dict] = {}


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
    settings_waiting_topic_name = State()
    settings_waiting_topic_id = State()


# Кеш топіків групи (оновлюємо по запиту)
TOPICS = {}


async def load_group_topics(bot) -> dict:
    """Спроба підвантажити гілки (forum topics) з групи.
    Якщо немає програмного способу — повертаємо попередньо відомі з налаштувань.
    """
    # Повертаємо мапу ім'я → thread_id з БД
    topics: dict[str, int] = {}
    rows = await db_manager.get_group_topics()
    for row in rows:
        topics[row.name] = row.thread_id
    return topics


@router.callback_query(F.data == "admin_broadcast")
async def broadcast_main_menu(callback: CallbackQuery, state: FSMContext):
    """Головне меню розсилки"""
    logger.info(f"🔔 Обробник broadcast_main_menu викликаний для користувача {callback.from_user.id}")
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
    await callback.message.edit_text(
        "📋 <b>Історія розсилок</b>\n\nФункція в розробці...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_broadcast")]
        ]),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "admin_broadcast_stats")
async def broadcast_stats(callback: CallbackQuery, state: FSMContext):
    """Статистика розсилок"""
    await callback.answer()
    await callback.message.edit_text(
        "📊 <b>Статистика розсилок</b>\n\nФункція в розробці...",
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
        group_id = message.media_group_id
        entry = _broadcast_media_groups.get(group_id)
        if not entry:
            entry = {
                'items': [],
                'chat_id': message.chat.id,
                'bot': message.bot,
                'state': state,
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
    await asyncio.sleep(delay)
    entry = _broadcast_media_groups.get(group_id)
    if not entry:
        return
    items: List[Dict] = entry['items']
    state: FSMContext = entry['state']
    # Зберігаємо у стані як media_group з масивом елементів
    await state.update_data(media={"type": "media_group", "items": items})
    # Очищаємо кеш
    del _broadcast_media_groups[group_id]
    # Показуємо підсумок
    bot = entry['bot']
    chat_id = entry['chat_id']
    await show_summary(Message(chat=message.chat, message_id=0, date=message.date, message_thread_id=None), state)


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
    if topic_part == "all":
        # Передаємо керування до відправки у всі гілки
        await send_to_all_topics(callback, state)
        return
    if topic_part == "general":
        # Відправка у головний топік (без thread_id)
        await _send_broadcast_to_chat(callback, state, thread_id=None)
        return
    
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

    buttons = None
    if button_text and button_url:
        buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=button_text, url=button_url)]])

    if not settings.group_chat_id:
        await callback.answer("❌ Не налаштовано group_chat_id", show_alert=True)
        return
    chat_id = settings.group_chat_id

    # Спочатку General
    errors = 0
    try:
        if media and media.get("type") == "photo":
            await callback.bot.send_photo(chat_id, media.get("file_id"), caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode())
        elif media and media.get("type") == "video":
            await callback.bot.send_video(chat_id, media.get("file_id"), caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode())
        elif media and media.get("type") == "media_group":
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            media_items = []
            for item in media.get("items", []):
                if item.get("type") == "photo":
                    media_items.append(InputMediaPhoto(media=item.get("file_id"), caption=text if not media_items else None, parse_mode=get_default_parse_mode()))
                elif item.get("type") == "video":
                    media_items.append(InputMediaVideo(media=item.get("file_id"), caption=text if not media_items else None, parse_mode=get_default_parse_mode()))
            if media_items:
                # Media group не підтримує inline-кнопки в Telegram API
                await callback.bot.send_media_group(chat_id, media=media_items, message_thread_id=thread_id)
                # Надішлемо окреме повідомлення з кнопкою, якщо є
                if buttons:
                    await callback.bot.send_message(chat_id, text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=thread_id)
            else:
                await callback.answer("❌ Порожня медіагрупа", show_alert=True)
                return
        else:
            await callback.bot.send_message(chat_id, text, reply_markup=buttons, parse_mode=get_default_parse_mode())
    except Exception:
        errors += 1

    # Потім усі гілки з БД
    for topic_id in TOPICS.values():
        try:
            if media and media.get("type") == "photo":
                await callback.bot.send_photo(chat_id, media.get("file_id"), caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=topic_id)
            elif media and media.get("type") == "video":
                await callback.bot.send_video(chat_id, media.get("file_id"), caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=topic_id)
            elif media and media.get("type") == "media_group":
                await callback.answer("❌ Медіагрупи поки не підтримуються", show_alert=True)
                return
            else:
                await callback.bot.send_message(chat_id, text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=topic_id)
        except Exception:
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

    # Зберігаємо розсилку в історію (чернетку → sent)
    await db_manager.create_broadcast({
        "text": text,
        "button_text": button_text,
        "button_url": button_url,
        "media_type": media.get("type") if media else None,
        "media_file_id": media.get("file_id") if media else None,
        "media_group_id": media.get("group_id") if media else None,
        "status": "sent",
    })

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
            await callback.bot.send_video(chat_id, media.get("file_id"), caption=text, reply_markup=buttons, parse_mode=get_default_parse_mode(), message_thread_id=thread_id)
        elif media and media.get("type") == "media_group":
            from aiogram.types import InputMediaPhoto, InputMediaVideo
            media_items = []
            for item in media.get("items", []):
                if item.get("type") == "photo":
                    media_items.append(InputMediaPhoto(media=item.get("file_id"), caption=text if not media_items else None, parse_mode=get_default_parse_mode()))
                elif item.get("type") == "video":
                    media_items.append(InputMediaVideo(media=item.get("file_id"), caption=text if not media_items else None, parse_mode=get_default_parse_mode()))
            if media_items:
                await callback.bot.send_media_group(chat_id, media=media_items)
                if buttons:
                    await callback.bot.send_message(chat_id, text, reply_markup=buttons, parse_mode=get_default_parse_mode())
            else:
                errors += 1
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


# ===== Блок налаштувань розсилки: додавання топіка групи =====

def _build_topics_menu_blocks(topics: list) -> tuple[str, InlineKeyboardMarkup]:
    """Повертає текст та клавіатуру для меню топіків (використовується повторно)."""
    lines = ["🧵 <b>Управління топіками</b>", "", "Збережені топіки:"]
    if topics:
        for t in topics:
            lines.append(f"• <b>{t.name}</b> (ID: <code>{t.thread_id}</code>)")
    else:
        lines.append("— Немає збережених топіків")

    kb_rows = [[InlineKeyboardButton(text="➕ Додати топік групи", callback_data="broadcast_settings_add_topic")]]
    if topics:
        kb_rows.append([InlineKeyboardButton(text="📋 Усі топіки", callback_data="broadcast_topics_list")])
    kb_rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_broadcast")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=kb_rows)


@router.callback_query(F.data == "admin_topics")
async def topics_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управління топіками (callback-версія)."""
    await callback.answer()
    topics = await db_manager.get_group_topics()
    text, keyboard = _build_topics_menu_blocks(topics)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=get_default_parse_mode())


@router.callback_query(F.data == "broadcast_settings_add_topic")
async def settings_add_topic_ask_name(callback: CallbackQuery, state: FSMContext):
    """Крок 1: Запит назви топіка"""
    await callback.answer()
    await state.update_data(new_topic_name=None, new_topic_id=None)
    await callback.message.edit_text(
        "🧩 <b>Додавання топіка</b>\n\nВведіть назву топіка (для відображення в меню):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_topics")]]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.settings_waiting_topic_name)


@router.message(BroadcastStates.settings_waiting_topic_name, F.text)
async def settings_add_topic_save_name(message: Message, state: FSMContext):
    """Зберегти назву та перейти до ID"""
    name = (message.text or "").strip()
    if not name:
        await message.answer("❌ Назва не може бути порожньою. Спробуйте ще раз.")
        return
    await state.update_data(new_topic_name=name)
    await message.answer(
        "🧵 Введіть thread_id (ID гілки у групі, наприклад: 55):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_settings_add_topic")]]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.settings_waiting_topic_id)


@router.message(BroadcastStates.settings_waiting_topic_id, F.text)
async def settings_add_topic_save_id(message: Message, state: FSMContext):
    """Зберегти ID, upsert у БД та повернутись у меню налаштувань"""
    text = (message.text or "").strip()
    try:
        thread_id = int(text)
        if thread_id <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Невірний thread_id. Вкажіть додатнє число, наприклад 55.")
        return

    data = await state.get_data()
    name = data.get("new_topic_name") or str(thread_id)

    await db_manager.upsert_group_topic(thread_id, name)

    # Опціонально: сформувати посилання, якщо є username групи
    link_hint = ""
    if getattr(settings, "group_username", None):
        link_hint = f"\n🔗 Можливе посилання: https://t.me/{settings.group_username}/{thread_id}"

    await message.answer(
        f"✅ Топік збережено: <b>{name}</b> (thread_id: <code>{thread_id}</code>){link_hint}",
        parse_mode=get_default_parse_mode(),
    )

    # Повернення до меню налаштувань без фейкового CallbackQuery
    await state.clear()
    topics = await db_manager.get_group_topics()
    text, keyboard = _build_topics_menu_blocks(topics)
    await message.answer(text, reply_markup=keyboard, parse_mode=get_default_parse_mode())


@router.callback_query(F.data == "broadcast_topics_list")
async def topics_list(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    topics = await db_manager.get_group_topics()
    if not topics:
        await callback.message.edit_text(
            "📋 <b>Усі топіки</b>\n\n— Немає збережених топіків",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_topics")]]),
            parse_mode=get_default_parse_mode(),
        )
        return
    kb = []
    for t in topics:
        kb.append([InlineKeyboardButton(text=f"{t.name} (ID: {t.thread_id})", callback_data=f"topic_view_{t.thread_id}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_topics")])
    await callback.message.edit_text(
        "📋 <b>Усі топіки</b>\n\nОберіть топік:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data.startswith("topic_view_"))
async def topic_view(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    thread_id = int(callback.data.split("_")[-1])
    topics = await db_manager.get_group_topics()
    topic = next((t for t in topics if t.thread_id == thread_id), None)
    if not topic:
        await callback.answer("❌ Топік не знайдено", show_alert=True)
        return
    text = (
        "🧵 <b>Топік</b>\n\n"
        f"<b>Назва:</b> {topic.name}\n"
        f"<b>ID:</b> <code>{topic.thread_id}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редагувати назву", callback_data=f"topic_rename_{topic.thread_id}")],
        [InlineKeyboardButton(text="🔢 Редагувати ID", callback_data=f"topic_changeid_{topic.thread_id}")],
        [InlineKeyboardButton(text="🗑️ Видалити", callback_data=f"topic_delete_{topic.thread_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_topics_list")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=get_default_parse_mode())


@router.callback_query(F.data.startswith("topic_delete_"))
async def settings_delete_topic(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    thread_id = int(callback.data.split("_")[-1])
    await db_manager.delete_group_topic(thread_id)
    await callback.answer("✅ Топік видалено", show_alert=True)
    await topics_list(callback, state)


@router.callback_query(F.data.startswith("topic_rename_"))
async def settings_rename_topic_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    thread_id = int(callback.data.split("_")[-1])
    await state.update_data(rename_thread_id=thread_id)
    await callback.message.edit_text(
        f"✏️ Введіть нову назву для топіка (ID: <code>{thread_id}</code>):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_topics_list")]]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.settings_waiting_topic_name)


@router.message(BroadcastStates.settings_waiting_topic_name, F.text)
async def settings_rename_topic_save(message: Message, state: FSMContext):
    data = await state.get_data()
    thread_id = data.get("rename_thread_id")
    if not thread_id:
        await message.answer("❌ Помилка стану. Спробуйте ще раз.")
        await state.clear()
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("❌ Назва не може бути порожньою.")
        return
    await db_manager.upsert_group_topic(thread_id, name)
    await message.answer("✅ Назву змінено")
    await state.clear()
    # Повернення до списку топіків без фейкового CallbackQuery
    topics = await db_manager.get_group_topics()
    if not topics:
        await message.answer(
            "📋 <b>Усі топіки</b>\n\n— Немає збережених топіків",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_topics")]]),
            parse_mode=get_default_parse_mode(),
        )
    else:
        kb = []
        for t in topics:
            kb.append([InlineKeyboardButton(text=f"{t.name} (ID: {t.thread_id})", callback_data=f"topic_view_{t.thread_id}")])
        kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_topics")])
        await message.answer(
            "📋 <b>Усі топіки</b>\n\nОберіть топік:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data.startswith("topic_changeid_"))
async def settings_change_topic_id_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    thread_id = int(callback.data.split("_")[-1])
    await state.update_data(changeid_old_thread_id=thread_id)
    await callback.message.edit_text(
        f"🔢 Введіть новий thread_id для топіка (поточний: <code>{thread_id}</code>):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="broadcast_topics_list")]]),
        parse_mode=get_default_parse_mode(),
    )
    await state.set_state(BroadcastStates.settings_waiting_topic_id)


@router.message(BroadcastStates.settings_waiting_topic_id, F.text)
async def settings_change_topic_id_save(message: Message, state: FSMContext):
    data = await state.get_data()
    old_thread_id = data.get("changeid_old_thread_id")
    # якщо це не зміна ID, то це може бути додавання (потік додавання вже оброблено вище)
    if not old_thread_id:
        # це шлях додавання — він вже обробляється у settings_add_topic_save_id
        return
    text = (message.text or "").strip()
    try:
        new_thread_id = int(text)
        if new_thread_id <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Невірний thread_id. Вкажіть додатнє число.")
        return
    await db_manager.update_group_topic_thread_id(old_thread_id, new_thread_id)
    await message.answer("✅ ID топіка змінено")
    await state.clear()
    # Повернення до списку топіків без фейкового CallbackQuery
    topics = await db_manager.get_group_topics()
    if not topics:
        await message.answer(
            "📋 <b>Усі топіки</b>\n\n— Немає збережених топіків",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_topics")]]),
            parse_mode=get_default_parse_mode(),
        )
    else:
        kb = []
        for t in topics:
            kb.append([InlineKeyboardButton(text=f"{t.name} (ID: {t.thread_id})", callback_data=f"topic_view_{t.thread_id}")])
        kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_topics")])
        await message.answer(
            "📋 <b>Усі топіки</b>\n\nОберіть топік:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode=get_default_parse_mode(),
        )

