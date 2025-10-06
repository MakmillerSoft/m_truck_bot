"""
Обробники пошуку авто
"""

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from app.modules.database.manager import db_manager
from app.modules.database.models import VehicleType, VehicleModel, VehicleCondition
from app.utils.formatting import (
    get_default_parse_mode,
    format_vehicle_characteristics,
    format_vehicle_card_with_photo,
)
from .keyboards import (
    get_search_keyboard,
    get_filter_keyboard,
    get_search_results_keyboard,
    get_engine_filter_keyboard,
    get_fuel_filter_keyboard,
    get_condition_filter_keyboard,
    get_capacity_filter_keyboard,
    get_sort_options_keyboard,
    get_filter_quick_keyboard,
    get_saved_vehicles_keyboard,
    get_saved_vehicle_detail_keyboard,
    get_search_history_keyboard,
    get_subscriptions_keyboard,
    get_vehicle_card_keyboard,
)
from .states import SearchStates


router = Router()


@router.message(F.text == "🔍 Пошук авто", StateFilter(None))
async def start_search(message: Message, state: FSMContext):
    """Початок пошуку авто"""
    await message.answer(
        "🔍 <b>Пошук вантажних авто</b>\n\n" "Оберіть спосіб пошуку:",
        reply_markup=get_search_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "quick_search")
async def quick_search(callback: CallbackQuery, state: FSMContext):
    """Всі авто - показати першу картку"""
    vehicles = await db_manager.get_vehicles(
        limit=50
    )  # Отримуємо більше авто для карток

    if not vehicles:
        await callback.message.edit_text(
            "❌ Наразі немає доступних авто.\n\n"
            "Спробуйте пізніше або зверніться до адміністрації.",
            parse_mode="HTML",
        )
        return

    # Зберігаємо список авто в стані для навігації
    await state.update_data(all_vehicles=vehicles, current_index=0)

    # Показуємо першу картку
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    user_id = user.id if user else None
    await show_vehicle_card(callback, vehicles[0], 0, len(vehicles), user_id)


async def show_vehicle_card_for_message(
    message: Message, vehicle, current_index: int, total_count: int, user_id: int = None
):
    """Показати картку авто для Message"""
    # Отримуємо головне фото авто
    main_photo = await db_manager.get_main_photo(vehicle.id)

    # Формуємо текст картки з фото
    text, photo_file_id = format_vehicle_card_with_photo(vehicle, main_photo)

    # Перевіряємо статус збереження
    is_saved = False
    if user_id:
        is_saved = await db_manager.is_vehicle_saved(user_id, vehicle.id)
        if is_saved:
            text += f"\n\n💾 <b>Збережено в обраному</b>"

    text += f"\n\n📊 <b>Картка {current_index + 1} з {total_count}</b>"

    # Визначаємо позицію авто
    is_first = current_index == 0
    is_last = current_index >= total_count - 1

    # Відправляємо повідомлення з фото або без
    if photo_file_id and (photo_file_id.startswith("BAAD") or photo_file_id.startswith("AgAC")):
        # Валідний Telegram file_id
        await message.answer_photo(
            photo=photo_file_id,
            caption=text,
            reply_markup=get_vehicle_card_keyboard(
                vehicle.id, is_first, is_last, is_saved
            ),
            parse_mode="HTML",
        )
    else:
        # Невалідний file_id або його немає - показуємо без фото
        await message.answer(
            text,
            reply_markup=get_vehicle_card_keyboard(
                vehicle.id, is_first, is_last, is_saved
            ),
            parse_mode="HTML",
        )


async def show_vehicle_card(
    callback: CallbackQuery,
    vehicle,
    current_index: int,
    total_count: int,
    user_id: int = None,
):
    """Показати картку авто"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Отримуємо головне фото авто
        main_photo = await db_manager.get_main_photo(vehicle.id)

        # Формуємо текст картки з фото
        text, photo_file_id = format_vehicle_card_with_photo(vehicle, main_photo)

        # Перевіряємо статус збереження
        is_saved = False
        if user_id:
            is_saved = await db_manager.is_vehicle_saved(user_id, vehicle.id)
            if is_saved:
                text += f"\n\n💾 <b>Збережено в обраному</b>"

        text += f"\n\n📊 <b>Картка {current_index + 1} з {total_count}</b>"

        # Визначаємо позицію авто
        is_first = current_index == 0
        is_last = current_index >= total_count - 1

        keyboard = get_vehicle_card_keyboard(vehicle.id, is_first, is_last, is_saved)

        # Правильна логіка пагінації: редагуємо існуюче повідомлення
        # Перевіряємо, чи поточне повідомлення містить фото
        has_photo = callback.message.photo is not None
        
        if photo_file_id and (photo_file_id.startswith("BAAD") or photo_file_id.startswith("AgAC")):
            # Валідний Telegram file_id
            if has_photo:
                # Поточне повідомлення містить фото - оновлюємо медіа
                try:
                    await callback.message.edit_media(
                        media=InputMediaPhoto(media=photo_file_id, caption=text, parse_mode="HTML"),
                        reply_markup=keyboard,
                    )
                except Exception as e:
                    if "message is not modified" in str(e):
                        # Контент не змінився - просто відповідаємо
                        await callback.answer()
                    else:
                        # Якщо не вдалося оновити медіа, видаляємо і створюємо нове
                        await callback.message.delete()
                        await callback.message.answer_photo(
                            photo=photo_file_id,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode="HTML",
                        )
            else:
                # Поточне повідомлення без фото - видаляємо і створюємо нове з фото
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=photo_file_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
        else:
            # Невалідний file_id або його немає - показуємо без фото
            if has_photo:
                # Поточне повідомлення містить фото - видаляємо і створюємо нове без фото
                await callback.message.delete()
                await callback.message.answer(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            else:
                # Поточне повідомлення без фото - оновлюємо текст
                try:
                    await callback.message.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML",
                    )
                except Exception as e:
                    if "message is not modified" in str(e):
                        # Контент не змінився - просто відповідаємо
                        await callback.answer()
                    else:
                        # Якщо не вдалося оновити, видаляємо і створюємо нове
                        await callback.message.delete()
                        await callback.message.answer(
                            text,
                            reply_markup=keyboard,
                            parse_mode="HTML",
                        )
            
    except Exception as e:
        logger.error(f"Помилка показу картки авто: {e}")
        # У разі помилки показуємо просте повідомлення
        try:
            await callback.message.edit_text(
                f"❌ Помилка завантаження авто: {str(e)}",
                parse_mode="HTML",
            )
        except:
            await callback.message.answer(
                f"❌ Помилка завантаження авто: {str(e)}",
                parse_mode="HTML",
            )


async def update_vehicle_card_after_save(
    callback: CallbackQuery,
    vehicle_id: int,
    user_id: int,
    is_saved: bool,
    state: FSMContext,
):
    """Оновити картку авто після збереження/видалення"""
    # Отримуємо поточні дані з FSM
    data = await state.get_data()
    vehicles = data.get("all_vehicles", [])
    current_index = data.get("current_index", 0)

    if not vehicles or current_index >= len(vehicles):
        return

    # Знаходимо поточне авто
    current_vehicle = vehicles[current_index]
    if current_vehicle.id != vehicle_id:
        return

    # Оновлюємо картку
    await show_vehicle_card(
        callback, current_vehicle, current_index, len(vehicles), user_id
    )


async def return_to_vehicle_card_from_message(
    message: Message, vehicle, current_index: int, total_count: int, user_id: int = None
):
    """Повернутися до картки авто з повідомлення (для Message обробників)"""
    # Отримуємо головне фото авто
    main_photo = await db_manager.get_main_photo(vehicle.id)

    # Формуємо текст картки з фото
    text, photo_file_id = format_vehicle_card_with_photo(vehicle, main_photo)

    # Перевіряємо статус збереження
    is_saved = False
    if user_id:
        is_saved = await db_manager.is_vehicle_saved(user_id, vehicle.id)
        if is_saved:
            text += f"\n\n💾 <b>Збережено в обраному</b>"

    text += f"\n\n📊 <b>Картка {current_index + 1} з {total_count}</b>"

    # Визначаємо позицію авто
    is_first = current_index == 0
    is_last = current_index >= total_count - 1

    # Відправляємо повідомлення з фото або без
    if photo_file_id and (photo_file_id.startswith("BAAD") or photo_file_id.startswith("AgAC")):
        # Валідний Telegram file_id
        await message.answer_photo(
            photo=photo_file_id,
            caption=text,
            reply_markup=get_vehicle_card_keyboard(
                vehicle.id, is_first, is_last, is_saved
            ),
            parse_mode="HTML",
        )
    else:
        # Невалідний file_id або його немає - показуємо без фото
        await message.answer(
            text,
            reply_markup=get_vehicle_card_keyboard(
                vehicle.id, is_first, is_last, is_saved
            ),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("next_vehicle_"))
async def next_vehicle(callback: CallbackQuery, state: FSMContext):
    """Показати наступне авто"""
    await callback.answer()

    data = await state.get_data()

    vehicles = data.get("all_vehicles", [])
    current_index = data.get("current_index", 0)

    if not vehicles or current_index >= len(vehicles) - 1:
        await callback.answer("❌ Немає більше авто для показу")
        return

    # Переходимо до наступного авто
    next_index = current_index + 1
    await state.update_data(current_index=next_index)

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    user_id = user.id if user else None
    await show_vehicle_card(
        callback, vehicles[next_index], next_index, len(vehicles), user_id
    )


@router.callback_query(F.data.startswith("prev_vehicle_"))
async def prev_vehicle(callback: CallbackQuery, state: FSMContext):
    """Показати попереднє авто"""
    await callback.answer()

    data = await state.get_data()

    vehicles = data.get("all_vehicles", [])
    current_index = data.get("current_index", 0)

    if not vehicles or current_index <= 0:
        await callback.answer("❌ Це перше авто в списку")
        return

    # Переходимо до попереднього авто
    prev_index = current_index - 1
    await state.update_data(current_index=prev_index)

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    user_id = user.id if user else None
    await show_vehicle_card(
        callback, vehicles[prev_index], prev_index, len(vehicles), user_id
    )


@router.callback_query(F.data.startswith("favorite_") & ~F.data.startswith("favorite_vehicle_"))
async def toggle_favorite(callback: CallbackQuery, state: FSMContext):
    """Зберегти авто в обране"""
    await callback.answer()

    vehicle_id = int(callback.data.split("_")[1])
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text(
            "❌ Користувач не знайдений. Будь ласка, зареєструйтесь."
        )
        return

    # Додаємо до збережених
    await db_manager.save_vehicle(user.id, vehicle_id)

    # Оновлюємо картку з новим статусом
    await update_vehicle_card_after_save(callback, vehicle_id, user.id, True, state)

    await callback.answer("✅ Авто додано до обраного", show_alert=True)


@router.callback_query(F.data.startswith("favorite_vehicle_"))
async def toggle_favorite_vehicle(callback: CallbackQuery, state: FSMContext):
    """Зберегти авто в обране (для 'Всі авто')"""
    await callback.answer()

    vehicle_id = int(callback.data.split("_")[2])
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text(
            "❌ Користувач не знайдений. Будь ласка, зареєструйтесь."
        )
        return

    try:
        # Додаємо до збережених
        await db_manager.save_vehicle(user.id, vehicle_id)
        
        # Оновлюємо картку з новим статусом
        await update_vehicle_card_after_save(callback, vehicle_id, user.id, True, state)
        
        await callback.answer("✅ Авто додано до обраного", show_alert=True)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Помилка збереження авто: {e}")
        await callback.answer("❌ Помилка збереження", show_alert=True)


@router.callback_query(F.data.startswith("unsave_") & ~F.data.startswith("unsave_vehicle_"))
async def unsave_vehicle(callback: CallbackQuery, state: FSMContext):
    """Видалити авто з обраного"""
    await callback.answer()

    vehicle_id = int(callback.data.split("_")[1])
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text(
            "❌ Користувач не знайдений. Будь ласка, зареєструйтесь."
        )
        return

    # Отримуємо поточні дані з FSM
    data = await state.get_data()
    vehicles = data.get("all_vehicles", [])
    current_index = data.get("current_index", 0)

    # Видаляємо з збережених
    await db_manager.remove_saved_vehicle(user.id, vehicle_id)

    # Видаляємо авто з поточного списку
    vehicles = [v for v in vehicles if v.id != vehicle_id]

    if not vehicles:
        # Якщо список порожній, повертаємося до головного меню
        await callback.message.edit_text(
            "📋 <b>Мої збережені авто</b>\n\n"
            "❌ У вас поки немає збережених авто.\n\n"
            "💡 <b>Як зберегти авто:</b>\n"
            "1. Знайдіть авто через 🔍 Пошук\n"
            "2. Натисніть ❤️ Зберегти\n"
            "3. Авто з'явиться в цьому розділі",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
        await state.clear()
        return

    # Коригуємо індекс, якщо потрібно
    if current_index >= len(vehicles):
        current_index = len(vehicles) - 1

    # Оновлюємо дані в FSM
    await state.update_data(all_vehicles=vehicles, current_index=current_index)

    # Показуємо оновлену картку
    await show_vehicle_card(
        callback, vehicles[current_index], current_index, len(vehicles), user.id
    )

    await callback.answer("❌ Авто видалено з обраного", show_alert=True)


@router.callback_query(F.data.startswith("contact_seller_"))
async def contact_seller(callback: CallbackQuery, state: FSMContext):
    """Залишити заявку на авто"""
    await callback.answer()

    vehicle_id = int(callback.data.split("_")[2])
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text(
            "❌ Користувач не знайдений. Будь ласка, зареєструйтесь."
        )
        return

    # Отримуємо інформацію про авто
    vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        await callback.message.edit_text("❌ Авто не знайдено")
        return

    # Зберігаємо ID авто в стані для заявки
    await state.update_data(selected_vehicle_id=vehicle_id)
    await state.set_state(SearchStates.waiting_for_contact_details)

    try:
        await callback.message.edit_text(
            f"📝 <b>Залишити заявку</b>\n\n"
            f"🚛 <b>Авто:</b> {vehicle.brand} {vehicle.model}\n"
            f"💰 <b>Ціна:</b> ${vehicle.price:,.0f}\n\n"
            f"💬 <b>Опишіть ваші питання або побажання:</b>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="❌ Скасувати", callback_data="cancel_contact"
                        )
                    ]
                ]
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        if "there is no text in the message to edit" in str(e):
            # Повідомлення містить фото - видаляємо і створюємо нове
            await callback.message.delete()
            await callback.message.answer(
                f"📝 <b>Залишити заявку</b>\n\n"
                f"🚛 <b>Авто:</b> {vehicle.brand} {vehicle.model}\n"
                f"💰 <b>Ціна:</b> ${vehicle.price:,.0f}\n\n"
                f"💬 <b>Опишіть ваші питання або побажання:</b>",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="❌ Скасувати", callback_data="cancel_contact"
                            )
                        ]
                    ]
                ),
                parse_mode="HTML",
            )
        else:
            raise e


@router.message(SearchStates.waiting_for_contact_details)
async def process_contact_details(message: Message, state: FSMContext):
    """Обробка деталей заявки на авто"""
    data = await state.get_data()
    vehicle_id = data.get("selected_vehicle_id")
    vehicles = data.get("all_vehicles", [])
    current_index = data.get("current_index", 0)

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

    # Створюємо заявку
    request_details = f"Запит щодо авто: {vehicle.brand} {vehicle.model} (ID: {vehicle_id})\n\n{message.text}"
    await db_manager.create_manager_request(user.id, "vehicle_inquiry", request_details)

    # Очищаємо тільки стан заявки, але зберігаємо дані навігації
    await state.set_state(None)
    await state.update_data(selected_vehicle_id=None)

    # Показуємо підтвердження та повертаємося до картки авто
    if vehicles and current_index < len(vehicles):
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        user_id = user.id if user else None

        # Показуємо підтвердження
        await message.answer(
            "✅ <b>Заявка створена!</b>\n\n"
            "Ваш запит передано менеджеру. Ми зв'яжемося з вами найближчим часом.\n\n"
            "💡 Ви можете переглянути всі заявки в розділі 'Всі заявки'",
            parse_mode="HTML",
        )

        # Повертаємося до картки авто через нове повідомлення
        await return_to_vehicle_card_from_message(
            message, vehicles[current_index], current_index, len(vehicles), user_id
        )
    else:
        await message.answer(
            "✅ <b>Заявка створена!</b>\n\n"
            "Ваш запит передано менеджеру. Ми зв'яжемося з вами найближчим часом.\n\n"
            "💡 Ви можете переглянути всі заявки в розділі 'Всі заявки'",
            parse_mode="HTML",
        )


@router.callback_query(F.data == "cancel_contact")
async def cancel_contact(callback: CallbackQuery, state: FSMContext):
    """Скасувати заявку"""
    await callback.answer()

    # Отримуємо дані ПЕРЕД очищенням стану
    data = await state.get_data()
    vehicles = data.get("all_vehicles", [])
    current_index = data.get("current_index", 0)

    # Очищаємо тільки стан заявки, але зберігаємо дані навігації
    await state.set_state(None)
    await state.update_data(selected_vehicle_id=None)

    # Повертаємося до картки авто
    if vehicles and current_index < len(vehicles):
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        user_id = user.id if user else None
        await show_vehicle_card(
            callback, vehicles[current_index], current_index, len(vehicles), user_id
        )
    else:
        await callback.message.edit_text(
            "🔍 <b>Пошук вантажних авто</b>\n\n" "Оберіть спосіб пошуку:",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "back_to_search")
async def back_to_search_from_cards(callback: CallbackQuery, state: FSMContext):
    """Повернутися до головного меню пошуку з карток"""
    await callback.answer()

    # Очищаємо стан
    await state.clear()

    try:
        await callback.message.edit_text(
            "🔍 <b>Пошук вантажних авто</b>\n\n" "Оберіть спосіб пошуку:",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
    except Exception as e:
        if "there is no text in the message to edit" in str(e):
            # Повідомлення містить фото - видаляємо і створюємо нове
            await callback.message.delete()
            await callback.message.answer(
                "🔍 <b>Пошук вантажних авто</b>\n\n" "Оберіть спосіб пошуку:",
                reply_markup=get_search_keyboard(),
                parse_mode="HTML",
            )
        else:
            raise e


@router.callback_query(F.data == "filter_search")
async def filter_search(callback: CallbackQuery):
    """Пошук з фільтрами"""
    await callback.message.edit_text(
        "🎛️ <b>Налаштування фільтрів</b>\n\n" "Оберіть параметри для пошуку:",
        reply_markup=get_filter_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("filter_"), StateFilter(None))
async def process_filter(callback: CallbackQuery, state: FSMContext):
    """Обробка фільтрів"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Перевіряємо, чи не знаходимося в стані створення авто
    current_state = await state.get_state()
    if current_state and "AdminVehicleStates" in str(current_state):
        logger.warning(f"Спроба використати фільтр під час створення авто. Стан: {current_state}")
        await callback.answer("⚠️ Завершіть створення авто перед пошуком")
        return
    
    filter_type = callback.data.split("_", 1)[1]

    if filter_type == "type":
        await callback.message.edit_text(
            "Оберіть тип авто:",
            reply_markup=get_vehicle_type_filter_keyboard(),
            parse_mode="HTML",
        )
    elif filter_type == "brand":
        await callback.message.edit_text(
            "Введіть марку авто (наприклад: Volvo):",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.waiting_for_brand)
    elif filter_type == "price":
        await callback.message.edit_text(
            "Введіть мінімальну ціну в USD (або /skip):",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.waiting_for_min_price)
    elif filter_type == "year":
        await callback.message.edit_text(
            "Введіть мінімальний рік (або /skip):", parse_mode="HTML"
        )
        await state.set_state(SearchStates.waiting_for_min_year)
    elif filter_type == "mileage":
        await callback.message.edit_text(
            "Введіть максимальний пробіг в км (або /skip):",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.waiting_for_max_mileage)
    elif filter_type == "location":
        await callback.message.edit_text(
            "Введіть місто або регіон:", parse_mode="HTML"
        )
        await state.set_state(SearchStates.waiting_for_location)
    elif filter_type == "engine":
        await callback.message.edit_text(
            "Оберіть тип двигуна:",
            reply_markup=get_engine_filter_keyboard(),
            parse_mode="HTML",
        )
    elif filter_type == "fuel":
        await callback.message.edit_text(
            "Оберіть тип палива:",
            reply_markup=get_fuel_filter_keyboard(),
            parse_mode="HTML",
        )
    elif filter_type == "condition":
        await callback.message.edit_text(
            "Оберіть стан авто:",
            reply_markup=get_condition_filter_keyboard(),
            parse_mode="HTML",
        )
    elif filter_type == "capacity":
        await callback.message.edit_text(
            "Оберіть вантажопідйомність:",
            reply_markup=get_capacity_filter_keyboard(),
            parse_mode="HTML",
        )
    elif filter_type == "sort":
        await callback.message.edit_text(
            "Оберіть сортування:",
            reply_markup=get_sort_options_keyboard(),
            parse_mode="HTML",
        )
    elif filter_type == "quick":
        await callback.message.edit_text(
            "Швидкі фільтри:",
            reply_markup=get_filter_quick_keyboard(),
            parse_mode="HTML",
        )
    elif filter_type == "apply":
        await apply_search_filters(callback, state)
    elif filter_type == "reset":
        await state.clear()
        await callback.message.edit_text(
            "🔄 Фільтри скинуто!\n\nОберіть нові параметри пошуку:",
            reply_markup=get_filter_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("search_type_"))
async def process_vehicle_type_filter(callback: CallbackQuery, state: FSMContext):
    """Обробка фільтру типу авто"""
    vehicle_type = callback.data.split("_", 2)[2]

    filters = {"vehicle_type": vehicle_type}
    vehicles = await db_manager.search_vehicles(filters)

    type_names = {
        "container_carrier": "Контейнеровози",
        "semi_container_carrier": "Напівпричепи контейнеровози",
        "variable_body": "Змінні кузови",
        "saddle_tractor": "Сідельні тягачі",
        "trailer": "Причепи",
        "refrigerator": "Рефрижератори",
        "van": "Фургони",
        "bus": "Буси",
    }

    title = f"{type_names.get(vehicle_type, 'Авто')} - знайдено {len(vehicles)}"
    await show_search_results(callback.message, vehicles, title, filters)


@router.message(SearchStates.waiting_for_brand)
async def process_brand_filter(message: Message, state: FSMContext):
    """Обробка фільтру марки"""
    brand = message.text.strip().title()

    filters = {"brand": brand}
    vehicles = await db_manager.search_vehicles(filters)

    await show_search_results(
        message, vehicles, f"Марка: {brand} - знайдено {len(vehicles)}", filters
    )
    await state.clear()


@router.message(SearchStates.waiting_for_min_price)
async def process_min_price(message: Message, state: FSMContext):
    """Обробка мінімальної ціни"""
    if message.text.strip() == "/skip":
        await message.answer(
            "Введіть максимальну ціну в USD (або /skip):",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.waiting_for_max_price)
        return

    try:
        min_price = float(message.text.strip().replace(",", "").replace("$", ""))
        await state.update_data(min_price=min_price)
        await message.answer(
            f"✅ Мінімальна ціна: ${min_price:,.0f}\n\nВведіть максимальну ціну (або /skip):",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.waiting_for_max_price)
    except ValueError:
        await message.answer(
            "❌ Введіть ціну числом (наприклад: 25000):",
            parse_mode="HTML",
        )


@router.message(SearchStates.waiting_for_max_price)
async def process_max_price(message: Message, state: FSMContext):
    """Обробка максимальної ціни"""
    data = await state.get_data()

    if message.text.strip() == "/skip":
        await apply_price_search(message, state, data.get("min_price"), None)
        return

    try:
        max_price = float(message.text.strip().replace(",", "").replace("$", ""))
        await apply_price_search(message, state, data.get("min_price"), max_price)
    except ValueError:
        await message.answer(
            "❌ Введіть ціну числом (наприклад: 50000):",
            parse_mode="HTML",
        )


async def apply_search_filters(callback: CallbackQuery, state: FSMContext):
    """Застосування всіх налаштованих фільтрів"""
    data = await state.get_data()

    if not data:
        await callback.message.edit_text(
            "❌ Немає налаштованих фільтрів.\n\nСпочатку оберіть параметри пошуку.",
            reply_markup=get_filter_keyboard(),
            parse_mode="HTML",
        )
        return

    vehicles = await db_manager.search_vehicles(data)
    title = f"Пошук з фільтрами - знайдено {len(vehicles)}"
    await show_search_results(callback.message, vehicles, title, data)
    await state.clear()


async def apply_price_search(
    message: Message,
    state: FSMContext,
    min_price: float = None,
    max_price: float = None,
):
    """Застосування пошуку за ціною"""
    filters = {}
    if min_price:
        filters["min_price"] = min_price
    if max_price:
        filters["max_price"] = max_price

    vehicles = await db_manager.search_vehicles(filters)

    price_text = ""
    if min_price and max_price:
        price_text = f"від ${min_price:,.0f} до ${max_price:,.0f}"
    elif min_price:
        price_text = f"від ${min_price:,.0f}"
    elif max_price:
        price_text = f"до ${max_price:,.0f}"

    title = f"Ціна {price_text} - знайдено {len(vehicles)}"
    await show_search_results(message, vehicles, title, filters)
    await state.clear()


async def show_search_results(
    message: Message, vehicles: list, title: str, search_params: dict = None
):
    """Показати результати пошуку"""
    # Зберігаємо пошук в історію, якщо є параметри
    if search_params and message.from_user:
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        if user:
            await db_manager.save_search_history(user.id, search_params, len(vehicles))

    if not vehicles:
        await message.answer(
            f"🔍 <b>{title}</b>\n\n"
            "❌ За вашими критеріями нічого не знайдено.\n\n"
            "Спробуйте змінити параметри пошуку.",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
        return

    # Показуємо перші 5 результатів
    results_text = f"🔍 <b>{title}</b>\n\n"

    for i, vehicle in enumerate(vehicles[:5], 1):
        results_text += (
            f"{i}. <b>{vehicle.brand} {vehicle.model}</b> ({vehicle.year})\n"
            f"   💰 ${vehicle.price:,.0f} | 📍 {vehicle.location or 'Не вказано'}\n"
        )
        if vehicle.mileage:
            results_text += f"   🛣️ {vehicle.mileage:,} км\n"
        results_text += "\n"

    if len(vehicles) > 5:
        results_text += f"\n... та ще {len(vehicles) - 5} авто\n"

    await message.answer(
        results_text,
        reply_markup=get_search_results_keyboard(vehicles[:10]),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("vehicle_details_"))
async def show_vehicle_details(callback: CallbackQuery):
    """Показати детальну інформацію про авто"""
    vehicle_id = int(callback.data.split("_")[2])

    await callback.answer()

    # Отримати авто з бази даних
    vehicles = await db_manager.get_vehicles()
    vehicle = next((v for v in vehicles if v.id == vehicle_id), None)

    if not vehicle:
        await callback.message.edit_text(
            "❌ <b>Авто не знайдено!</b>\n\n"
            "Можливо, оголошення було видалено або змінено.",
            parse_mode="HTML",
        )
        return

    # Перевірити чи збережено користувачем
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    is_saved = False
    if user:
        is_saved = await db_manager.is_vehicle_saved(user.id, vehicle_id)

    # Форматування детальної інформації
    from app.modules.group.config import get_vehicle_emoji, get_condition_emoji

    type_emoji = get_vehicle_emoji(vehicle.vehicle_type.value)
    condition_emoji = get_condition_emoji(vehicle.condition.value)

    # Назви стану
    condition_names = {
        "new": "Новий",
        "excellent": "Відмінний",
        "good": "Хороший",
        "fair": "Задовільний",
        "poor": "Поганий",
        "for_parts": "На запчастини",
    }
    condition_name = condition_names.get(
        vehicle.condition.value, vehicle.condition.value
    )

    # Назви типів
    type_names = {
        "container_carrier": "Контейнеровоз",
        "semi_container_carrier": "Напівпричіп контейнеровоз",
        "variable_body": "Змінний кузов",
        "saddle_tractor": "Сідельний тягач",
        "trailer": "Причіп",
        "refrigerator": "Рефрижератор",
        "van": "Фургон",
        "bus": "Бус",
    }
    type_name = type_names.get(vehicle.vehicle_type.value, vehicle.vehicle_type.value)

    detail_text = f"""
{type_emoji} <b>{vehicle.brand} {vehicle.model}</b>

📋 <b>Основна інформація:</b>
• Тип: {type_name}
• Рік випуску: {vehicle.year}
• Стан: {condition_emoji} {condition_name}
• Ціна: <b>${vehicle.price:,.0f}</b>
• Валюта: {vehicle.currency}
"""

    if vehicle.mileage:
        detail_text += f"• Пробіг: {vehicle.mileage:,} км\n"

    if vehicle.location:
        detail_text += f"• Місцезнаходження: {vehicle.location}\n"

    # Технічні характеристики
    if any(
        [
            vehicle.engine_type,
            vehicle.engine_volume,
            vehicle.power_hp,
            vehicle.transmission,
            vehicle.fuel_type,
            vehicle.load_capacity,
        ]
    ):
        detail_text += "\n🔧 <b>Технічні характеристики:</b>\n"

        if vehicle.engine_type:
            detail_text += f"• Двигун: {vehicle.engine_type}"
            if vehicle.engine_volume:
                detail_text += f" ({vehicle.engine_volume}л)"
            detail_text += "\n"

        if vehicle.power_hp:
            detail_text += f"• Потужність: {vehicle.power_hp} к.с.\n"

        if vehicle.transmission:
            detail_text += f"• Коробка передач: {vehicle.transmission}\n"

        if vehicle.fuel_type:
            detail_text += f"• Тип палива: {vehicle.fuel_type}\n"

        if vehicle.load_capacity:
            detail_text += f"• Вантажопідйомність: {vehicle.load_capacity} кг\n"

    # Опис
    if vehicle.description:
        detail_text += f"\n📝 <b>Опис:</b>\n{vehicle.description}\n"

    # Контактна інформація
    detail_text += f"""

📞 <b>Контакти:</b>
• Телефон: +380 66 372 69 41
• Компанія: M-Truck Company

🆔 <b>ID авто:</b> #{vehicle.id}
📅 <b>Додано:</b> {vehicle.created_at.strftime('%d.%m.%Y')}
"""

    # Створити клавіатуру
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = []

    if user:
        if is_saved:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="💔 Видалити з збережених",
                        callback_data=f"unsave_vehicle_{vehicle_id}",
                    )
                ]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="❤️ Зберегти авто",
                        callback_data=f"save_vehicle_{vehicle_id}",
                    )
                ]
            )

    keyboard.extend(
        [
            [
                InlineKeyboardButton(text="📞 Контакти", callback_data="show_contacts"),
                InlineKeyboardButton(text="📧 Email", callback_data="show_email"),
            ],
            [
                InlineKeyboardButton(
                    text="📋 Залишити заявку",
                    callback_data=f"contact_seller_{vehicle_id}",
                ),
                InlineKeyboardButton(
                    text="💬 Чат з менеджером", callback_data="chat_manager"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад до результатів", callback_data="back_to_search"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        detail_text.strip(),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("save_vehicle_"))
async def save_vehicle_for_user(callback: CallbackQuery):
    """Зберегти авто для користувача"""
    vehicle_id = int(callback.data.split("_")[2])

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Спочатку зареєструйтеся!")
        return

    try:
        await db_manager.save_vehicle(user.id, vehicle_id)
        await callback.answer("✅ Авто збережено!")

        # Оновити кнопку
        await show_vehicle_details(callback)

    except Exception as e:
        await callback.answer("❌ Помилка збереження!")


@router.callback_query(F.data.startswith("unsave_vehicle_"))
async def unsave_vehicle_for_user(callback: CallbackQuery, state: FSMContext):
    """Видалити авто з збережених (для 'Всі авто')"""
    vehicle_id = int(callback.data.split("_")[2])

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Користувач не знайдений!")
        return

    try:
        await db_manager.remove_saved_vehicle(user.id, vehicle_id)
        
        # Оновлюємо картку з новим статусом
        await update_vehicle_card_after_save(callback, vehicle_id, user.id, False, state)
        
        await callback.answer("💔 Авто видалено з збережених!", show_alert=True)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Помилка видалення авто: {e}")
        await callback.answer("❌ Помилка видалення!", show_alert=True)


def get_vehicle_type_filter_keyboard():
    """Клавіатура фільтру типу авто"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = [
        [
            InlineKeyboardButton(
                text="📦 Контейнеровози", callback_data="search_type_container_carrier"
            ),
            InlineKeyboardButton(
                text="🚚 Напівпричепи контейнеровози",
                callback_data="search_type_semi_container_carrier",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔄 Змінні кузови", callback_data="search_type_variable_body"
            ),
            InlineKeyboardButton(
                text="🚛 Сідельні тягачі", callback_data="search_type_saddle_tractor"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🚜 Причепи", callback_data="search_type_trailer"
            ),
            InlineKeyboardButton(
                text="❄️ Рефрижератори", callback_data="search_type_refrigerator"
            ),
        ],
        [
            InlineKeyboardButton(text="🚐 Фургони", callback_data="search_type_van"),
            InlineKeyboardButton(text="🚌 Буси", callback_data="search_type_bus"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="filter_search")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == "📋 Мої збережені", StateFilter(None))
async def show_saved_vehicles(message: Message, state: FSMContext):
    """Показати збережені авто користувача"""
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode="HTML",
        )
        return

    # Отримуємо збережені авто як повні об'єкти VehicleModel
    saved_vehicles_data = await db_manager.get_saved_vehicles(user.id)

    if not saved_vehicles_data:
        await message.answer(
            "📋 <b>Мої збережені авто</b>\n\n"
            "❌ У вас поки немає збережених авто.\n\n"
            "💡 <b>Як зберегти авто:</b>\n"
            "1. Знайдіть авто через 🔍 Пошук\n"
            "2. Натисніть ❤️ Зберегти\n"
            "3. Авто з'явиться в цьому розділі",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
        return

    # Отримуємо повні об'єкти авто
    vehicles = []
    for saved_vehicle in saved_vehicles_data:
        # saved_vehicle вже містить всі дані авто через JOIN
        # Створюємо VehicleModel з цих даних
        try:
            vehicle = VehicleModel(
                id=saved_vehicle["id"],
                vin_code=saved_vehicle.get("vin_code"),
                brand=saved_vehicle["brand"],
                model=saved_vehicle["model"],
                year=saved_vehicle["year"],
                vehicle_type=VehicleType(saved_vehicle["vehicle_type"]),
                condition=VehicleCondition(saved_vehicle["condition"]),
                price=saved_vehicle["price"],
                currency=saved_vehicle.get("currency", "USD"),
                mileage=saved_vehicle.get("mileage"),
                engine_volume=saved_vehicle.get("engine_volume"),
                power_hp=saved_vehicle.get("power_hp"),
                wheel_radius=saved_vehicle.get("wheel_radius"),
                body_type=saved_vehicle.get("body_type"),
                fuel_type=saved_vehicle.get("fuel_type"),
                transmission=saved_vehicle.get("transmission"),
                load_capacity=saved_vehicle.get("load_capacity"),
                total_weight=saved_vehicle.get("total_weight"),
                cargo_dimensions=saved_vehicle.get("cargo_dimensions"),
                location=saved_vehicle.get("location"),
                description=saved_vehicle.get("description"),
                seller_id=saved_vehicle["seller_id"],
                created_at=(
                    datetime.fromisoformat(saved_vehicle["created_at"])
                    if saved_vehicle.get("created_at")
                    else datetime.now()
                ),
                updated_at=(
                    datetime.fromisoformat(saved_vehicle["updated_at"])
                    if saved_vehicle.get("updated_at")
                    else datetime.now()
                ),
            )
            vehicles.append(vehicle)
        except Exception as e:
            print(f"Помилка створення VehicleModel: {e}")
            continue

    if not vehicles:
        await message.answer(
            "📋 <b>Мої збережені авто</b>\n\n"
            "❌ Збережені авто не знайдені в базі даних.",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
        return

    # Зберігаємо список авто в стані для навігації
    await state.update_data(all_vehicles=vehicles, current_index=0)

    # Показуємо першу картку
    await show_vehicle_card_for_message(message, vehicles[0], 0, len(vehicles), user.id)


async def show_saved_vehicles_for_callback(callback: CallbackQuery, state: FSMContext):
    """Показати збережені авто для callback (для кнопок Назад)"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode="HTML",
        )
        return

    # Отримуємо збережені авто як повні об'єкти VehicleModel
    saved_vehicles_data = await db_manager.get_saved_vehicles(user.id)

    if not saved_vehicles_data:
        await callback.message.edit_text(
            "📋 <b>Мої збережені авто</b>\n\n"
            "❌ У вас поки немає збережених авто.\n\n"
            "💡 <b>Як зберегти авто:</b>\n"
            "1. Знайдіть авто через 🔍 Пошук\n"
            "2. Натисніть ❤️ Зберегти\n"
            "3. Авто з'явиться в цьому розділі",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
        return

    # Отримуємо повні об'єкти авто
    vehicles = []
    for saved_vehicle in saved_vehicles_data:
        # saved_vehicle вже містить всі дані авто через JOIN
        # Створюємо VehicleModel з цих даних
        try:
            vehicle = VehicleModel(
                id=saved_vehicle["id"],
                vin_code=saved_vehicle.get("vin_code"),
                brand=saved_vehicle["brand"],
                model=saved_vehicle["model"],
                year=saved_vehicle["year"],
                vehicle_type=VehicleType(saved_vehicle["vehicle_type"]),
                condition=VehicleCondition(saved_vehicle["condition"]),
                price=saved_vehicle["price"],
                currency=saved_vehicle.get("currency", "USD"),
                mileage=saved_vehicle.get("mileage"),
                engine_volume=saved_vehicle.get("engine_volume"),
                power_hp=saved_vehicle.get("power_hp"),
                wheel_radius=saved_vehicle.get("wheel_radius"),
                body_type=saved_vehicle.get("body_type"),
                fuel_type=saved_vehicle.get("fuel_type"),
                transmission=saved_vehicle.get("transmission"),
                load_capacity=saved_vehicle.get("load_capacity"),
                total_weight=saved_vehicle.get("total_weight"),
                cargo_dimensions=saved_vehicle.get("cargo_dimensions"),
                location=saved_vehicle.get("location"),
                description=saved_vehicle.get("description"),
                seller_id=saved_vehicle["seller_id"],
                created_at=(
                    datetime.fromisoformat(saved_vehicle["created_at"])
                    if saved_vehicle.get("created_at")
                    else datetime.now()
                ),
                updated_at=(
                    datetime.fromisoformat(saved_vehicle["updated_at"])
                    if saved_vehicle.get("updated_at")
                    else datetime.now()
                ),
            )
            vehicles.append(vehicle)
        except Exception as e:
            print(f"Помилка створення VehicleModel: {e}")
            continue

    if not vehicles:
        await callback.message.edit_text(
            "📋 <b>Мої збережені авто</b>\n\n"
            "❌ Збережені авто не знайдені в базі даних.",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
        return

    # Зберігаємо список авто в стані для навігації
    await state.update_data(all_vehicles=vehicles, current_index=0)

    # Показуємо першу картку
    await show_vehicle_card(callback, vehicles[0], 0, len(vehicles), user.id)


@router.callback_query(F.data == "show_email")
async def show_email_info(callback: CallbackQuery):
    """Показати email інформацію"""
    await callback.answer("📧 Email: info@mtruck.ua")


# ===== НОВІ ОБРОБНИКИ ФІЛЬТРІВ =====


@router.callback_query(F.data.startswith("engine_"))
async def process_engine_filter(callback: CallbackQuery, state: FSMContext):
    """Обробка фільтру двигуна"""
    engine_type = callback.data.split("_", 1)[1]

    if engine_type == "any":
        await state.update_data(engine_type=None)
    else:
        await state.update_data(engine_type=engine_type)

    await callback.answer(f"✅ Двигун: {engine_type}")
    await callback.message.edit_text(
        "Фільтри налаштовано! Оберіть наступний параметр:",
        reply_markup=get_filter_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("fuel_"))
async def process_fuel_filter(callback: CallbackQuery, state: FSMContext):
    """Обробка фільтру палива"""
    fuel_type = callback.data.split("_", 1)[1]

    if fuel_type == "any":
        await state.update_data(fuel_type=None)
    else:
        await state.update_data(fuel_type=fuel_type)

    await callback.answer(f"✅ Паливо: {fuel_type}")
    await callback.message.edit_text(
        "Фільтри налаштовано! Оберіть наступний параметр:",
        reply_markup=get_filter_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("condition_"))
async def process_condition_filter(callback: CallbackQuery, state: FSMContext):
    """Обробка фільтру стану авто"""
    condition = callback.data.split("_", 1)[1]

    if condition == "any":
        await state.update_data(condition=None)
    else:
        await state.update_data(condition=condition)

    await callback.answer(f"✅ Стан: {condition}")
    await callback.message.edit_text(
        "Фільтри налаштовано! Оберіть наступний параметр:",
        reply_markup=get_filter_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("capacity_"))
async def process_capacity_filter(callback: CallbackQuery, state: FSMContext):
    """Обробка фільтру вантажопідйомності"""
    capacity = callback.data.split("_", 1)[1]

    if capacity == "any":
        await state.update_data(load_capacity=None)
    else:
        # Встановлюємо діапазони вантажопідйомності
        capacity_ranges = {
            "light": (0, 3500),
            "medium": (3500, 7500),
            "heavy": (7500, 16000),
            "extra_heavy": (16000, 999999),
        }

        if capacity in capacity_ranges:
            min_capacity, max_capacity = capacity_ranges[capacity]
            await state.update_data(
                min_load_capacity=min_capacity, max_load_capacity=max_capacity
            )

    await callback.answer(f"✅ Вантажопідйомність: {capacity}")
    await callback.message.edit_text(
        "Фільтри налаштовано! Оберіть наступний параметр:",
        reply_markup=get_filter_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("sort_"))
async def process_sort_filter(callback: CallbackQuery, state: FSMContext):
    """Обробка сортування"""
    sort_type = callback.data.split("_", 1)[1]

    await state.update_data(sort_by=sort_type)
    await callback.answer(f"✅ Сортування: {sort_type}")
    await callback.message.edit_text(
        "Сортування налаштовано! Оберіть наступний параметр:",
        reply_markup=get_filter_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("quick_filter_"), StateFilter(None))
async def process_quick_filter(callback: CallbackQuery, state: FSMContext):
    """Обробка швидких фільтрів"""
    # Перевіряємо, чи не знаходимося в стані створення авто
    current_state = await state.get_state()
    if current_state and "AdminVehicleStates" in str(current_state):
        await callback.answer("⚠️ Завершіть створення авто перед пошуком")
        return
    
    filter_type = callback.data.split("_", 2)[2]

    # Очищаємо попередні фільтри
    await state.clear()

    if filter_type == "new":
        await state.update_data(min_year=2020, condition="new")
    elif filter_type == "cheap":
        await state.update_data(max_price=30000)
    elif filter_type == "premium":
        await state.update_data(min_price=50000, condition="excellent")
    elif filter_type == "ukraine":
        await state.update_data(location="Україна")
    elif filter_type == "trucks":
        await state.update_data(vehicle_type="truck")

    await callback.answer(f"✅ Швидкий фільтр: {filter_type}")

    # Застосовуємо фільтри
    data = await state.get_data()
    vehicles = await db_manager.search_vehicles(data)
    title = f"Швидкий пошук - знайдено {len(vehicles)}"
    await show_search_results(callback.message, vehicles, title, data)
    await state.clear()


@router.callback_query(F.data == "back_to_filters")
async def back_to_filters(callback: CallbackQuery):
    """Повернутися до фільтрів"""
    await callback.answer()

    # Перевіряємо реєстрацію користувача
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        "🎛️ <b>Фільтри пошуку</b>\n\nОберіть параметри:",
        reply_markup=get_filter_keyboard(),
        parse_mode="HTML",
    )


# ===== ОБРОБНИКИ ЗБЕРЕЖЕНИХ АВТО =====


@router.callback_query(F.data.startswith("saved_vehicle_"))
async def show_saved_vehicle_details(callback: CallbackQuery):
    """Показати деталі збереженого авто"""
    vehicle_id = int(callback.data.split("_")[2])

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Користувач не знайдений!")
        return

    # Отримуємо деталі авто
    vehicles = await db_manager.get_vehicles(limit=1000)  # Отримуємо всі авто
    vehicle = next((v for v in vehicles if v.id == vehicle_id), None)

    if not vehicle:
        await callback.answer("❌ Авто не знайдено!")
        return

    # Отримуємо нотатки користувача
    saved_vehicles = await db_manager.get_saved_vehicles(user.id)
    saved_vehicle = next((sv for sv in saved_vehicles if sv["id"] == vehicle_id), None)

    text = f"🚛 <b>{vehicle.brand} {vehicle.model}</b> ({vehicle.year})\n\n"
    text += f"💰 <b>Ціна:</b> ${vehicle.price:,.0f}\n"
    text += f"📍 <b>Місцезнаходження:</b> {vehicle.location or 'Не вказано'}\n"
    text += f"🛣️ <b>Пробіг:</b> {vehicle.mileage:,} км\n" if vehicle.mileage else ""
    text += f"🔧 <b>Двигун:</b> {vehicle.engine_type or 'Не вказано'}\n"
    text += f"⛽ <b>Паливо:</b> {vehicle.fuel_type or 'Не вказано'}\n"
    text += (
        f"📦 <b>Вантажопідйомність:</b> {vehicle.load_capacity:,} кг\n"
        if vehicle.load_capacity
        else ""
    )
    text += f"⭐ <b>Стан:</b> {vehicle.condition}\n"

    if saved_vehicle and saved_vehicle.get("notes"):
        text += f"\n📝 <b>Ваші нотатки:</b>\n{saved_vehicle['notes']}\n"

    if vehicle.description:
        text += f"\n📄 <b>Опис:</b>\n{vehicle.description}\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_saved_vehicle_detail_keyboard(vehicle_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "back_to_saved")
async def back_to_saved_vehicles(callback: CallbackQuery, state: FSMContext):
    """Повернутися до збережених авто"""
    await callback.answer()

    # Перевіряємо реєстрацію користувача
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode="HTML",
        )
        return

    await show_saved_vehicles_for_callback(callback, state)


@router.callback_query(F.data == "back_to_results")
async def back_to_search_results(callback: CallbackQuery):
    """Повернутися до результатів пошуку"""
    await callback.answer()

    # Перевіряємо реєстрацію користувача
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode="HTML",
        )
        return

    # Показуємо останні результати пошуку або швидкий пошук
    from .keyboards import get_search_keyboard

    await callback.message.edit_text(
        "🔍 <b>Результати пошуку</b>\n\n" "Оберіть спосіб пошуку:",
        reply_markup=get_search_keyboard(),
        parse_mode="HTML",
    )


# ===== ІСТОРІЯ ПОШУКІВ =====


@router.callback_query(F.data == "saved_searches")
async def show_search_history(callback: CallbackQuery):
    """Показати історію пошуків користувача"""
    await callback.answer()

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode="HTML",
        )
        return

    search_history = await db_manager.get_search_history(user.id, limit=10)

    if not search_history:
        await callback.message.edit_text(
            "📋 <b>Останні пошуки</b>\n\n"
            "❌ У вас поки немає пошуків.\n\n"
            "💡 <b>Як це працює:</b>\n"
            "1. Виконайте пошук авто з фільтрами\n"
            "2. Ваші пошуки автоматично збережуться\n"
            "3. Тут ви зможете їх швидко повторити",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
        return

    text = f"📋 <b>Останні пошуки</b> ({len(search_history)})\n\n"

    for i, search in enumerate(search_history, 1):
        created_date = search["created_at"][:10] if search["created_at"] else "Невідомо"
        results_text = (
            f"({search['results_count']} результатів)"
            if search["results_count"] > 0
            else "(без результатів)"
        )

        text += f"{i}. <b>{search['search_name']}</b>\n"
        text += f"   📅 {created_date} | {results_text}\n\n"

    text += "💡 <b>Натисніть на пошук, щоб повторити його</b>"

    await callback.message.edit_text(
        text,
        reply_markup=get_search_history_keyboard(search_history),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("repeat_search_"))
async def repeat_search_from_history(callback: CallbackQuery):
    """Повторити пошук з історії"""
    await callback.answer()

    search_id = int(callback.data.split("_", 2)[2])

    # Отримуємо параметри пошуку з історії
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        return

    search_history = await db_manager.get_search_history(user.id, limit=100)
    search_data = next((s for s in search_history if s["id"] == search_id), None)

    if not search_data:
        await callback.message.edit_text("❌ Пошук не знайдено")
        return

    # Формуємо параметри пошуку
    search_params = {
        "vehicle_type": search_data.get("vehicle_type"),
        "brand": search_data.get("brand"),
        "min_year": search_data.get("min_year"),
        "max_year": search_data.get("max_year"),
        "min_price": search_data.get("min_price"),
        "max_price": search_data.get("max_price"),
        "max_mileage": search_data.get("max_mileage"),
        "location": search_data.get("location"),
        "engine_type": search_data.get("engine_type"),
        "fuel_type": search_data.get("fuel_type"),
        "load_capacity": search_data.get("load_capacity"),
        "condition": search_data.get("condition"),
    }

    # Виконуємо пошук
    vehicles = await db_manager.search_vehicles(search_params)

    if not vehicles:
        await callback.message.edit_text(
            f"🔍 <b>Повторний пошук</b>\n\n"
            f"❌ За критеріями '{search_data['search_name']}' нічого не знайдено.\n\n"
            f"💡 Спробуйте змінити параметри пошуку",
            reply_markup=get_search_keyboard(),
            parse_mode="HTML",
        )
        return

    # Показуємо результати
    text = f"🔍 <b>Результати пошуку</b>\n\n"
    text += f"📋 Критерії: {search_data['search_name']}\n"
    text += f"📊 Знайдено: {len(vehicles)} авто\n\n"

    for i, vehicle in enumerate(vehicles[:10], 1):
        text += f"{i}. <b>{vehicle.brand} {vehicle.model}</b> ({vehicle.year})\n"
        text += f"   💰 ${vehicle.price:,.0f} | 📍 {vehicle.location or 'Не вказано'}\n"
        if vehicle.mileage:
            text += f"   🛣️ {vehicle.mileage:,} км\n"
        text += "\n"

    if len(vehicles) > 10:
        text += f"... та ще {len(vehicles) - 10} авто\n\n"

    text += "💡 <b>Натисніть на авто для деталей</b>"

    await callback.message.edit_text(
        text,
        reply_markup=get_search_results_keyboard(vehicles),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "clear_search_history")
async def clear_search_history(callback: CallbackQuery):
    """Очистити історію пошуків"""
    await callback.answer()

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        return

    await db_manager.delete_search_history(user.id)

    await callback.message.edit_text(
        "🗑️ <b>Історія пошуків очищена</b>\n\n" "Всі ваші попередні пошуки видалені.",
        reply_markup=get_search_keyboard(),
        parse_mode="HTML",
    )


# ===== ПІДПИСКИ =====


@router.callback_query(F.data == "search_subscriptions")
async def show_subscriptions(callback: CallbackQuery):
    """Показати підписки користувача"""
    await callback.answer()

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode="HTML",
        )
        return

    subscriptions = await db_manager.get_user_subscriptions(user.id)

    if not subscriptions:
        await callback.message.edit_text(
            "🔔 <b>Сповіщення про нові авто</b>\n\n"
            "❌ У вас поки немає підписок.\n\n"
            "💡 <b>Як це працює:</b>\n"
            "1. Налаштуйте пошук з фільтрами\n"
            "2. Створіть підписку на ці критерії\n"
            "3. Отримуйте сповіщення про нові авто\n\n"
            "🔔 <b>Натисніть 'Створити підписку' щоб почати</b>",
            reply_markup=get_subscriptions_keyboard([]),
            parse_mode="HTML",
        )
        return

    text = f"🔔 <b>Мої підписки</b> ({len(subscriptions)})\n\n"

    for i, sub in enumerate(subscriptions, 1):
        status_icon = "✅" if sub["is_active"] else "❌"
        created_date = sub["created_at"][:10] if sub["created_at"] else "Невідомо"

        text += f"{i}. {status_icon} <b>{sub['subscription_name']}</b>\n"
        text += f"   📅 Створено: {created_date}\n"
        if sub["last_notification"]:
            last_notif = sub["last_notification"][:10]
            text += f"   🔔 Останнє сповіщення: {last_notif}\n"
        text += "\n"

    text += "💡 <b>Натисніть на підписку для керування</b>"

    await callback.message.edit_text(
        text,
        reply_markup=get_subscriptions_keyboard(subscriptions),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "create_subscription")
async def create_subscription_menu(callback: CallbackQuery):
    """Меню створення підписки"""
    await callback.answer()

    await callback.message.edit_text(
        "🔔 <b>Створення підписки</b>\n\n"
        "💡 <b>Як створити підписку:</b>\n"
        "1. Налаштуйте пошук з фільтрами\n"
        "2. Натисніть 'Отримувати сповіщення'\n"
        "3. Дайте назву підписці\n"
        "4. Готово! Ви отримуватимете сповіщення\n\n"
        "🎯 <b>Спочатку виконайте пошук з фільтрами</b>",
        reply_markup=get_search_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("subscription_"))
async def manage_subscription(callback: CallbackQuery):
    """Керування підпискою"""
    await callback.answer()

    action = callback.data.split("_", 1)[1]

    if action.startswith("toggle_"):
        subscription_id = int(action.split("_", 1)[1])
        # Тут буде логіка перемикання статусу підписки
        await callback.message.edit_text("🔄 Статус підписки змінено")

    elif action.startswith("delete_"):
        subscription_id = int(action.split("_", 1)[1])
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if user:
            await db_manager.delete_subscription(user.id, subscription_id)
            await callback.message.edit_text("🗑️ Підписку видалено")

    # Показуємо оновлений список підписок
    await show_subscriptions(callback)


@router.message(F.text.startswith("/start vehicle_"))
async def handle_vehicle_link(message: Message, state: FSMContext):
    """Обробка посилання на авто з заявки"""
    try:
        # Витягуємо ID авто з команди
        vehicle_id = int(message.text.split("vehicle_")[1])

        # Отримуємо авто з БД
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            await message.answer("❌ Авто не знайдено")
            return

        # Отримуємо всі авто для навігації
        all_vehicles = await db_manager.get_all_vehicles()

        # Знаходимо позицію поточного авто в списку
        current_index = 0
        for i, v in enumerate(all_vehicles):
            if v.id == vehicle_id:
                current_index = i
                break

        # Отримуємо користувача
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        user_id = user.id if user else None

        # Показуємо картку авто
        await show_vehicle_card_for_message(
            message, vehicle, current_index, len(all_vehicles), user_id
        )

    except (ValueError, IndexError):
        await message.answer("❌ Невірне посилання на авто")
    except Exception as e:
        await message.answer("❌ Помилка при завантаженні авто")
