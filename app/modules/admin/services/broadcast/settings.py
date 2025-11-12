"""
Налаштування топіків для розсилки (адмін)
Управління гілками групи
"""
import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from app.utils.formatting import get_default_parse_mode
from app.config.settings import settings
from app.modules.database.manager import db_manager
from .handlers import BroadcastStates, load_group_topics

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast_settings")
router.message.filter(AdminAccessFilter())
router.callback_query.filter(AdminAccessFilter())


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
    data = await state.get_data()
    
    # Перевіряємо чи це зміна ID (є changeid_old_thread_id)
    if data.get("changeid_old_thread_id"):
        # Це зміна ID - передаємо контроль до settings_change_topic_id_save
        await settings_change_topic_id_save(message, state)
        return
    
    # Це додавання нового топіка
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
    # Примусово оновлюємо кеш топіків після додавання
    await load_group_topics(message.bot, force_refresh=True)

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
    # Примусово оновлюємо кеш топіків після видалення
    await load_group_topics(callback.bot, force_refresh=True)
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
    await state.set_state(BroadcastStates.settings_waiting_rename_topic_name)


@router.message(BroadcastStates.settings_waiting_rename_topic_name, F.text)
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
    # Примусово оновлюємо кеш топіків після зміни назви
    await load_group_topics(message.bot, force_refresh=True)
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
    # Примусово оновлюємо кеш топіків після зміни ID
    await load_group_topics(message.bot, force_refresh=True)
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


