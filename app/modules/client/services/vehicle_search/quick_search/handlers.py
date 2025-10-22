import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.utils.formatting import get_default_parse_mode
from app.modules.client.services.authentication.registration.keyboards import get_main_menu_inline_keyboard
from app.modules.database.manager import db_manager
from .formatters import format_client_vehicle_card
from .states import ClientSearchStates
from . import quick_search_router as router

logger = logging.getLogger(__name__)

@router.callback_query(F.data == "client_catalog_menu")
async def show_catalog_menu(callback: CallbackQuery, state: FSMContext):
    """Проміжне меню каталогу: показує заголовок, кількість авто та 2 кнопки"""
    await callback.answer()
    await state.clear()
    try:
        total = await db_manager.get_available_vehicles_count()
    except Exception:
        total = 0
    text = (
        "🚛 <b>Каталог авто</b>\n\n"
        f"Доступно авто: <b>{total}</b>\n\n"
        "Оберіть дію нижче:"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Всі авто", callback_data="client_catalog")],
            [InlineKeyboardButton(text="🔍 Пошук по параметрах", callback_data="client_search")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")],
        ]
    )
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=get_default_parse_mode())
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=keyboard, parse_mode=get_default_parse_mode())


def get_quick_search_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для меню швидкого пошуку"""
    keyboard = [
        [InlineKeyboardButton(text="🏷️🚗 Пошук по марці та моделі", callback_data="client_advanced_search")],
        [InlineKeyboardButton(text="📅 Пошук по роках", callback_data="client_search_years")],
        [InlineKeyboardButton(text="💰 Пошук по вартості", callback_data="client_search_price")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="client_catalog_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_vehicle_card_keyboard(
    vehicle_id: int,
    is_first: bool = False,
    is_last: bool = False,
    is_saved: bool = False,
    group_message_id: int = None,
) -> InlineKeyboardMarkup:
    """Клавіатура для картки авто в режимі 'Всі авто'"""
    # Динамічна кнопка збереження
    save_button_text = "💔 Видалити з обраного" if is_saved else "❤️ Зберегти"
    save_button_callback = (
        f"unsave_vehicle_{vehicle_id}" if is_saved else f"favorite_vehicle_{vehicle_id}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                text=save_button_text, callback_data=save_button_callback
            ),
            InlineKeyboardButton(
                text="📝 Залишити заявку", callback_data=f"contact_seller_{vehicle_id}"
            ),
        ]
    ]

    # Кнопка "Перейти в групу" якщо авто опубліковано
    if group_message_id:
        from app.config.settings import settings
        if settings.group_chat_id:
            group_chat_id = settings.group_chat_id.replace('@', '')
            group_link = f"https://t.me/{group_chat_id}/{group_message_id}"
            keyboard.append([
                InlineKeyboardButton(
                    text="👥 Перейти в групу",
                    url=group_link
                )
            ])

    # Кнопки навігації
    nav_buttons = []
    if not is_first:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Попереднє авто", callback_data=f"prev_vehicle_{vehicle_id}"
            )
        )
    if not is_last:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Наступне авто", callback_data=f"next_vehicle_{vehicle_id}"
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка переходу до параметричного пошуку
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔍 Пошук по параметрах", callback_data="client_search"
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="client_catalog_menu"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def show_vehicle_card(
    callback: CallbackQuery, vehicle, current_index: int, total_count: int, user_id: int = None
):
    """Показати картку авто для CallbackQuery"""
    from .utils import check_group_message_exists
    
    # Перевіряємо існування повідомлення в групі (якщо авто опубліковано)
    group_message_id = None
    if vehicle.published_in_group and vehicle.group_message_id:
        from app.config.settings import settings
        if settings.group_chat_id:
            message_exists = await check_group_message_exists(callback.bot, settings.group_chat_id, vehicle.group_message_id)
            
            if not message_exists:
                # Повідомлення не існує - очищаємо дані в БД
                await db_manager.update_vehicle(vehicle.id, {
                    'group_message_id': None,
                    'published_in_group': False
                })
                logger.info(f"🔄 Авто {vehicle.id}: повідомлення в групі не існує, статус оновлено")
            else:
                # Повідомлення існує - передаємо ID для кнопки
                group_message_id = vehicle.group_message_id
    
    # Форматуємо картку
    text, photo_file_id = format_client_vehicle_card(vehicle)

    # Перевіряємо статус збереження
    is_saved = False
    if user_id:
        is_saved = await db_manager.is_vehicle_saved(user_id, vehicle.id)

    # Визначаємо позицію авто
    is_first = current_index == 0
    is_last = current_index == total_count - 1

    # Отримуємо клавіатуру з group_message_id
    keyboard = get_vehicle_card_keyboard(vehicle.id, is_first, is_last, is_saved, group_message_id)

    # Відправляємо картку
    if photo_file_id:
        try:
            # Визначаємо тип: video:... чи звичайне фото
            is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
            file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
            if is_video:
                from aiogram.types import InputMediaVideo
                await callback.message.edit_media(
                    media=InputMediaVideo(
                        media=file_id,
                        caption=text,
                        parse_mode=get_default_parse_mode()
                    ),
                    reply_markup=keyboard
                )
            else:
                from aiogram.types import InputMediaPhoto
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=file_id,
                        caption=text,
                        parse_mode=get_default_parse_mode()
                    ),
                    reply_markup=keyboard
                )
        except Exception:
            # Якщо не вдалось - видаляємо і створюємо нове
            try:
                await callback.message.delete()
            except Exception:
                pass
            if is_video:
                await callback.message.answer_video(
                    video=file_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=get_default_parse_mode()
                )
            else:
                await callback.message.answer_photo(
                    photo=file_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=get_default_parse_mode()
                )
    else:
        # Без фото - просто текст
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode()
            )
        except Exception:
            # Якщо не вдалось редагувати - видаляємо і створюємо нове
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(
                text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode()
            )


async def show_vehicle_card_message(
    message: Message, vehicle, current_index: int, total_count: int, user_id: int = None
):
    """Показати картку авто для Message (без CallbackQuery)"""
    from .utils import check_group_message_exists
    
    # Перевіряємо існування повідомлення в групі (якщо авто опубліковано)
    group_message_id = None
    if vehicle.published_in_group and vehicle.group_message_id:
        from app.config.settings import settings
        if settings.group_chat_id:
            message_exists = await check_group_message_exists(message.bot, settings.group_chat_id, vehicle.group_message_id)
            if not message_exists:
                await db_manager.update_vehicle(vehicle.id, {
                    'group_message_id': None,
                    'published_in_group': False
                })
                logger.info(f"🔄 Авто {vehicle.id}: повідомлення в групі не існує, статус оновлено")
            else:
                group_message_id = vehicle.group_message_id

    # Форматуємо картку
    text, photo_file_id = format_client_vehicle_card(vehicle)

    # Перевіряємо статус збереження
    is_saved = False
    if user_id:
        is_saved = await db_manager.is_vehicle_saved(user_id, vehicle.id)

    # Визначаємо позицію авто
    is_first = current_index == 0
    is_last = current_index == total_count - 1

    # Отримуємо клавіатуру з group_message_id
    keyboard = get_vehicle_card_keyboard(vehicle.id, is_first, is_last, is_saved, group_message_id)

    # Відправляємо картку
    if photo_file_id:
        is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
        file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
        if is_video:
            await message.answer_video(
                video=file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode()
            )
        else:
            await message.answer_photo(
                photo=file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode()
            )
    else:
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode=get_default_parse_mode()
        )

@router.callback_query(F.data == "client_search")
async def show_quick_search(callback: CallbackQuery, state: FSMContext):
    """Показати меню швидкого пошуку"""
    await callback.answer()
    await state.clear()
    
    text = "🔍 <b>Швидкий пошук авто</b>\n\nОберіть дію нижче або поверніться назад."
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_quick_search_menu_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        # Якщо не вдалось редагувати (можливо фото) - видаляємо і створюємо нове
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            text,
            reply_markup=get_quick_search_menu_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data == "client_catalog")
async def quick_search(callback: CallbackQuery, state: FSMContext):
    """Всі авто - показати першу картку"""
    await callback.answer()
    
    vehicles = await db_manager.get_available_vehicles(limit=50)

    if not vehicles:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")]
            ]
        )
        try:
            await callback.message.edit_text(
                "❌ Наразі немає доступних авто.\n\n"
                "Спробуйте пізніше або поверніться до головного меню.",
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode(),
            )
        except Exception:
            await callback.message.answer(
                "❌ Наразі немає доступних авто.\n\n"
                "Спробуйте пізніше або поверніться до головного меню.",
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode(),
            )
        return

    # Зберігаємо список авто в стані для навігації
    await state.update_data(all_vehicles=vehicles, current_index=0)

    # Показуємо першу картку
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    user_id = user.id if user else None
    await show_vehicle_card(callback, vehicles[0], 0, len(vehicles), user_id)


@router.callback_query(F.data.startswith("prev_vehicle_"))
async def prev_vehicle(callback: CallbackQuery, state: FSMContext):
    """Попереднє авто"""
    await callback.answer()
    
    data = await state.get_data()
    vehicles = data.get("all_vehicles", [])
    current_index = data.get("current_index", 0)

    if not vehicles or current_index == 0:
        await callback.answer("Це перше авто", show_alert=False)
        return

    new_index = current_index - 1
    await state.update_data(current_index=new_index)

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    user_id = user.id if user else None
    await show_vehicle_card(callback, vehicles[new_index], new_index, len(vehicles), user_id)


@router.callback_query(F.data.startswith("next_vehicle_"))
async def next_vehicle(callback: CallbackQuery, state: FSMContext):
    """Наступне авто"""
    await callback.answer()
    
    data = await state.get_data()
    vehicles = data.get("all_vehicles", [])
    current_index = data.get("current_index", 0)

    if not vehicles or current_index >= len(vehicles) - 1:
        await callback.answer("Це останнє авто", show_alert=False)
        return

    new_index = current_index + 1
    await state.update_data(current_index=new_index)

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    user_id = user.id if user else None
    await show_vehicle_card(callback, vehicles[new_index], new_index, len(vehicles), user_id)


@router.callback_query(F.data.startswith("favorite_vehicle_"))
async def toggle_favorite_vehicle(callback: CallbackQuery, state: FSMContext):
    """Зберегти авто в обране (для 'Всі авто')"""
    vehicle_id = int(callback.data.split("_")[2])
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("❌ Спочатку зареєструйтеся!", show_alert=True)
        return

    try:
        # Додаємо до збережених
        await db_manager.save_vehicle(user.id, vehicle_id)
        
        # Оновлюємо картку з новим статусом
        data = await state.get_data()
        vehicles = data.get("all_vehicles", [])
        current_index = data.get("current_index", 0)
        
        if vehicles and current_index < len(vehicles):
            await show_vehicle_card(callback, vehicles[current_index], current_index, len(vehicles), user.id)
        
        await callback.answer("✅ Авто додано до обраного", show_alert=True)
    except Exception as e:
        logger.error(f"Помилка збереження авто: {e}")
        await callback.answer("❌ Помилка збереження", show_alert=True)


@router.callback_query(F.data.startswith("unsave_vehicle_"))
async def unsave_vehicle(callback: CallbackQuery, state: FSMContext):
    """Видалити авто з обраного"""
    vehicle_id = int(callback.data.split("_")[2])
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("❌ Користувач не знайдений", show_alert=True)
        return

    try:
        # Видаляємо зі збережених
        await db_manager.remove_saved_vehicle(user.id, vehicle_id)
        
        # Оновлюємо картку з новим статусом
        data = await state.get_data()
        vehicles = data.get("all_vehicles", [])
        current_index = data.get("current_index", 0)
        
        if vehicles and current_index < len(vehicles):
            await show_vehicle_card(callback, vehicles[current_index], current_index, len(vehicles), user.id)
        
        await callback.answer("❌ Авто видалено з обраного", show_alert=True)
    except Exception as e:
        logger.error(f"Помилка видалення авто: {e}")
        await callback.answer("❌ Помилка видалення", show_alert=True)


@router.callback_query(F.data.startswith("client_view_vehicle_"))
async def view_vehicle_from_subscription(callback: CallbackQuery, state: FSMContext):
    """Переглянути конкретне авто (з підписки)"""
    await callback.answer()
    
    try:
        # Витягуємо ID авто з callback_data
        vehicle_id = int(callback.data.split("_")[3])
        
        # Отримуємо авто з бази
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            await callback.answer("❌ Авто не знайдено", show_alert=True)
            return
        
        # Перевіряємо, чи авто не продане
        if vehicle.status == 'sold':
            await callback.answer("❌ Це авто вже продане", show_alert=True)
            return
        
        # Отримуємо користувача
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        user_id = user.id if user else None
        
        # Отримуємо всі авто для навігації
        vehicles = await db_manager.get_available_vehicles(limit=50)
        
        # Знаходимо індекс поточного авто
        current_index = 0
        for i, v in enumerate(vehicles):
            if v.id == vehicle_id:
                current_index = i
                break
        
        # Зберігаємо в state для навігації
        await state.update_data(all_vehicles=vehicles, current_index=current_index)
        
        # Показуємо картку авто
        await show_vehicle_card(callback, vehicle, current_index, len(vehicles), user_id)
        
        logger.info(f"👁️ Користувач {callback.from_user.id} переглядає авто {vehicle_id} з підписки")
        
    except Exception as e:
        logger.error(f"❌ Помилка відкриття авто: {e}", exc_info=True)
        await callback.answer("❌ Помилка відкриття авто", show_alert=True)


@router.callback_query(F.data.startswith("contact_seller_"))
async def contact_seller(callback: CallbackQuery, state: FSMContext):
    """Залишити заявку на авто"""
    vehicle_id = int(callback.data.split("_")[2])
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("❌ Спочатку зареєструйтеся!", show_alert=True)
        return

    # Отримуємо інформацію про авто
    vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        await callback.answer("❌ Авто не знайдено", show_alert=True)
        return

    # Зберігаємо ID авто в стані для заявки
    await state.update_data(selected_vehicle_id=vehicle_id)
    await state.set_state(ClientSearchStates.waiting_for_application_details)

    try:
        brand = vehicle.brand or "Не вказано"
        model = vehicle.model or "Не вказано"
        if vehicle.price is not None:
            try:
                price_display = f"${float(vehicle.price):,.0f}"
            except Exception:
                price_display = "Не вказано"
        else:
            price_display = "Не вказано"
        await callback.message.edit_text(
            f"📝 <b>Залишити заявку</b>\n\n"
            f"🚛 <b>Авто:</b> {brand} {model}\n"
            f"💰 <b>Ціна:</b> {price_display}\n\n"
            f"💬 <b>Опишіть ваші питання або побажання:</b>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_application")]
                ]
            ),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        # Повідомлення містить фото - видаляємо і створюємо нове
        await callback.message.delete()
        brand = vehicle.brand or "Не вказано"
        model = vehicle.model or "Не вказано"
        if vehicle.price is not None:
            try:
                price_display = f"${float(vehicle.price):,.0f}"
            except Exception:
                price_display = "Не вказано"
        else:
            price_display = "Не вказано"
        await callback.message.answer(
            f"📝 <b>Залишити заявку</b>\n\n"
            f"🚛 <b>Авто:</b> {brand} {model}\n"
            f"💰 <b>Ціна:</b> {price_display}\n\n"
            f"💬 <b>Опишіть ваші питання або побажання:</b>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_application")]
                ]
            ),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data == "cancel_application")
async def cancel_application(callback: CallbackQuery, state: FSMContext):
    """Скасувати заявку"""
    await state.clear()
    await callback.answer("❌ Заявку скасовано")
    await callback.message.edit_text(
        "🏠 <b>Головне меню</b>\n\nОберіть розділ:",
        reply_markup=get_main_menu_inline_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.message(ClientSearchStates.waiting_for_application_details, F.text)
async def process_application_details(message: Message, state: FSMContext):
    """Обробка деталей заявки на авто"""
    from app.config.settings import settings
    
    logger.info(f"📝 Отримано текст повідомлення від користувача {message.from_user.id}")
    logger.info(f"📝 Обробка заявки на авто в ClientSearchStates.waiting_for_application_details")
    
    data = await state.get_data()
    vehicle_id = data.get("selected_vehicle_id")
    
    if not vehicle_id:
        await message.answer("❌ Помилка: авто не вибрано")
        await state.clear()
        return
    
    # Отримуємо користувача з БД
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("❌ Помилка! Користувач не знайдений.")
        await state.clear()
        return
    
    # Отримуємо інформацію про авто
    vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        await message.answer("❌ Авто не знайдено")
        await state.clear()
        return
    
    # Зберігаємо заявку в БД
    try:
        await db_manager.create_manager_request(user_id=user.id, request_type="vehicle_application", details=message.text or "", vehicle_id=vehicle.id)
    except Exception:
        pass

    # Формуємо повідомлення для адміністратора
    brand = vehicle.brand or "Не вказано"
    model = vehicle.model or "Не вказано"
    if vehicle.price is not None:
        try:
            price_display = f"${float(vehicle.price):,.0f}"
        except Exception:
            price_display = "Не вказано"
    else:
        price_display = "Не вказано"

    admin_message = (
        f"📝 <b>Нова заявка на авто</b>\n\n"
        f"👤 <b>Від користувача:</b>\n"
        f"• Ім'я: {user.first_name or 'Не вказано'}\n"
        f"• Телефон: {user.phone or 'Не вказано'}\n"
        f"• Telegram ID: <code>{user.telegram_id}</code>\n\n"
        f"🚛 <b>Авто:</b> {brand} {model}\n"
        f"💰 <b>Ціна:</b> {price_display}\n\n"
        f"💬 <b>Повідомлення:</b>\n{message.text or ''}"
    )
    
    # Надсилаємо повідомлення всім адміністраторам без порушення станів
    for admin_id in settings.get_admin_ids():
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Перейти до заявок", callback_data="admin_requests")]])
            await message.bot.send_message(admin_id, admin_message, reply_markup=kb, parse_mode=get_default_parse_mode())
        except Exception:
            pass
    
    # Підтверджуємо користувачу
    await message.answer(
        "✅ <b>Заявку надіслано!</b>\n\n"
        "Наш менеджер зв'яжеться з вами найближчим часом.\n"
        "Дякуємо за звернення!",
        reply_markup=get_main_menu_inline_keyboard(),
        parse_mode=get_default_parse_mode(),
    )
    
    await state.clear()
