"""
Підсумкова картка авто
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from .states import VehicleCreationStates
from ..editing.states import VehicleEditingStates

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())


def get_summary_card_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для підсумкової картки авто"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Редагувати", callback_data="edit_vehicle_card")],
            [InlineKeyboardButton(text="📤 Опублікувати", callback_data="show_publication_options")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_vehicle_creation")]
        ]
    )


def get_publication_options_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура з опціями публікації"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 В бот", callback_data="publish_to_bot_only")],
            [InlineKeyboardButton(text="👥 В групу", callback_data="publish_to_group_only")],
            [InlineKeyboardButton(text="🚀 В бот та групу", callback_data="publish_to_both")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_summary_card")]
        ]
    )


from ..shared.translations import translate_field_value


def format_vehicle_summary(data: dict) -> str:
    """Форматування підсумкової картки авто"""
    # Список полів для відображення
    fields = [
        ("Тип авто", "vehicle_type"),
        ("Марка", "brand"),
        ("Модель", "model"),
        ("VIN код", "vin_code"),
        ("Тип кузова", "body_type"),
        ("Рік випуску", "year"),
        ("Стан", "condition"),
        ("Вартість", "price", "USD"),
        ("Пробіг", "mileage", "км"),
        ("Тип палива", "fuel_type"),
        ("Об'єм двигуна", "engine_volume", "л"),
        ("Потужність", "power_hp", "кВт"),
        ("Коробка передач", "transmission"),
        ("Радіус коліс", "wheel_radius"),
        ("Вантажопідйомність", "load_capacity", "кг"),
        ("Загальна маса", "total_weight", "кг"),
        ("Габарити вантажного відсіку", "cargo_dimensions"),
        ("Місцезнаходження", "location"),
        ("Опис", "description")
    ]
    
    summary_lines = ["🚛 <b>Картка авто створена!</b>", ""]
    
    # Додаємо тільки заповнені поля
    for field_name, field_key, *unit in fields:
        value = data.get(field_key)
        if value and value != 'Не вказано':
            # Перевіряємо, чи це рядок і чи не порожній після strip()
            if isinstance(value, str) and not value.strip():
                continue
            # Якщо це не рядок (наприклад, int), просто перевіряємо, чи не порожній
            elif not isinstance(value, str) and not value:
                continue
            
            # Перекладаємо значення якщо потрібно
            translated_value = translate_field_value(field_key, str(value))
                
            unit_text = f" {unit[0]}" if unit else ""
            summary_lines.append(f"✅ <b>{field_name}:</b> {translated_value}{unit_text}")
    
    # Додаємо інформацію про фото
    main_photo = data.get('main_photo')
    group_photos = data.get('group_photos', [])
    if main_photo:
        summary_lines.append(f"✅ <b>Головне фото:</b> додано")
    if group_photos:
        summary_lines.append(f"✅ <b>Фото для групи:</b> {len(group_photos)} шт.")
    
    summary_lines.extend(["", "<b>Картка готова до публікації!</b>"])
    
    return "\n".join(summary_lines)


async def create_summary_card_with_photo(callback: CallbackQuery, state: FSMContext) -> None:
    """Створення підсумкової картки з фото"""
    data = await state.get_data()
    main_photo = data.get('main_photo')
    group_photos = data.get('group_photos', [])
    
    if not (main_photo or (group_photos and len(group_photos) > 0)):
        await callback.message.answer(
            "❌ Потрібно завантажити хоча б одне фото авто",
            reply_markup=get_summary_card_keyboard()
        )
        return
    
    # Форматуємо текст підсумкової картки
    summary_text = format_vehicle_summary(data)
    
    # Вибираємо фото для прев'ю в боті: головне, або перше з фото для групи
    first_photo = main_photo or (group_photos[0] if group_photos else None)
    
    # Клавіатура
    summary_keyboard = get_summary_card_keyboard()
    
    logger.info(f"📷 create_summary_card_with_photo: використовуємо фото для картки в боті: {'main_photo' if main_photo else 'group_photos[0]'}")
    
    # Відправляємо повідомлення з медіа та текстом (фото або відео)
    try:
        is_video = isinstance(first_photo, str) and first_photo.startswith("video:")
        file_id = first_photo.split(":", 1)[1] if is_video else first_photo
        if is_video:
            try:
                await callback.message.answer_video(
                    video=file_id,
                    caption=summary_text,
                    reply_markup=summary_keyboard,
                    parse_mode="HTML"
                )
            except Exception as video_error:
                logger.warning(f"⚠️ Не вдалося відправити відео для картки: {video_error}")
                # Якщо відео недійсне, відправляємо тільки текст
                await callback.message.answer(
                    summary_text,
                    reply_markup=summary_keyboard,
                    parse_mode="HTML"
                )
        else:
            try:
                await callback.message.answer_photo(
                    photo=file_id,
                    caption=summary_text,
                    reply_markup=summary_keyboard,
                    parse_mode="HTML"
                )
            except Exception as photo_error:
                logger.warning(f"⚠️ Не вдалося відправити фото для картки: {photo_error}")
                # Якщо фото недійсне, відправляємо тільки текст
                await callback.message.answer(
                    summary_text,
                    reply_markup=summary_keyboard,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"📷 Помилка відправки фото: {e}")
        # Якщо не вдалося відправити фото, відправляємо тільки текст
        await callback.message.answer(
            text=summary_text,
            reply_markup=summary_keyboard,
            parse_mode="HTML"
        )
    
    # Переходимо до стану підсумкової картки
    await state.set_state(VehicleCreationStates.summary_card)
    
    logger.info(f"📷 Створено підсумкову картку з фото для користувача {callback.from_user.id}")


async def edit_summary_card_message(callback: CallbackQuery, state: FSMContext) -> None:
    """Редагування існуючого повідомлення в підсумкову картку"""
    data = await state.get_data()
    main_photo = data.get('main_photo')
    group_photos = data.get('group_photos', [])
    
    if not (main_photo or (group_photos and len(group_photos) > 0)):
        await callback.message.answer(
            "❌ Потрібно завантажити хоча б одне фото авто",
            reply_markup=get_summary_card_keyboard()
        )
        return
    
    # Форматуємо текст підсумкової картки
    summary_text = format_vehicle_summary(data)
    
    # Вибираємо фото для прев'ю в боті
    first_photo = main_photo or (group_photos[0] if group_photos else None)
    
    # Клавіатура
    summary_keyboard = get_summary_card_keyboard()
    
    logger.info(f"📷 edit_summary_card_message: використовуємо фото для картки в боті: {'main_photo' if main_photo else 'group_photos[0]'}")
    
    # Отримуємо ID повідомлення для редагування
    last_photos_message_id = data.get('last_group_photos_message_id')
    last_additional_photos_message_id = data.get('last_additional_group_photos_message_id')
    message_to_edit_id = last_additional_photos_message_id or last_photos_message_id
    
    try:
        if message_to_edit_id:
            # Намагаємося редагувати медіа (фото + підпис)
            try:
                from aiogram.types import InputMediaPhoto, InputMediaVideo
                is_video = isinstance(first_photo, str) and first_photo.startswith("video:")
                file_id = first_photo.split(":", 1)[1] if is_video else first_photo
                media = InputMediaVideo(media=file_id, caption=summary_text, parse_mode="HTML") if is_video else InputMediaPhoto(media=file_id, caption=summary_text, parse_mode="HTML")
                await callback.message.bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=message_to_edit_id,
                    media=media,
                    reply_markup=summary_keyboard
                )
                logger.info(f"📷 Підсумкова картка з медіа відредагована в повідомленні {message_to_edit_id}")
            except Exception as edit_error:
                logger.warning(f"📷 Не вдалося редагувати медіа повідомлення: {edit_error}")
                # Якщо не вдалося редагувати медіа, спробуємо редагувати тільки текст
                try:
                    await callback.message.bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=message_to_edit_id,
                        text=summary_text,
                        reply_markup=summary_keyboard,
                        parse_mode="HTML"
                    )
                    logger.info(f"📷 Підсумкова картка (тільки текст) відредагована в повідомленні {message_to_edit_id}")
                except Exception as text_edit_error:
                    logger.warning(f"📷 Не вдалося редагувати текст повідомлення: {text_edit_error}")
                    # Якщо не вдалося редагувати, створюємо нове повідомлення з фото
                    await create_summary_card_with_photo(callback, state)
                    return
        else:
            # Якщо немає повідомлення для редагування, створюємо нове
            await create_summary_card_with_photo(callback, state)
            return
            
    except Exception as e:
        logger.warning(f"📷 Не вдалося редагувати повідомлення: {e}")
        # Якщо не вдалося редагувати, створюємо нове
        await create_summary_card_with_photo(callback, state)
        return
    
    # Переходимо до стану підсумкової картки
    await state.set_state(VehicleCreationStates.summary_card)


@router.callback_query(F.data == "finish_vehicle_creation")
async def finish_vehicle_creation(callback: CallbackQuery, state: FSMContext):
    """Завершення створення картки авто"""
    await callback.answer()
    
    # Отримуємо всі дані
    data = await state.get_data()
    
    # Перевіряємо наявність головного фото або фото для групи
    main_photo = data.get('main_photo')
    group_photos = data.get('group_photos', [])
    if not (main_photo or (group_photos and len(group_photos) > 0)):
        await callback.message.answer(
            "❌ Потрібно завантажити хоча б одне фото авто",
            reply_markup=get_summary_card_keyboard()
        )
        return
    
    # Створюємо підсумкову картку
    await edit_summary_card_message(callback, state)


@router.callback_query(F.data == "edit_vehicle_card")
async def edit_vehicle_card(callback: CallbackQuery, state: FSMContext):
    """Редагування картки авто"""
    await callback.answer()
    
    # Імпортуємо обробник редагування
    from ..editing.handlers import show_editing_menu
    
    # Викликаємо обробник редагування
    await show_editing_menu(callback, state)


@router.callback_query(F.data == "show_publication_options")
async def show_publication_options(callback: CallbackQuery, state: FSMContext):
    """Показати опції публікації"""
    await callback.answer()
    
    try:
        # Отримуємо дані для перевірки
        data = await state.get_data()
        
        # Перевіряємо обов'язкові поля: тип авто, головне фото та фото для групи
        vehicle_type_present = bool(data.get('vehicle_type'))
        has_main_photo = bool(data.get('main_photo'))
        has_group_photos = len(data.get('group_photos', [])) > 0
        missing_fields = []
        if not vehicle_type_present:
            missing_fields.append('Тип авто')
        if not has_main_photo:
            missing_fields.append('Головне фото')
        if not has_group_photos:
            missing_fields.append('Фото для групи')
        
        if missing_fields:
            error_text = f"❌ <b>Помилки публікації:</b>\n\n❌ Помилка валідації: Поле '{missing_fields[0]}' є обов'язковим; Потрібно хоча б одне фото"
            
            if callback.message.photo:
                from aiogram.types import InputMediaPhoto
                media = InputMediaPhoto(
                    media=callback.message.photo[-1].file_id,
                    caption=error_text,
                    parse_mode="HTML"
                )
                await callback.message.edit_media(media=media)
            elif callback.message.video:
                from aiogram.types import InputMediaVideo
                media = InputMediaVideo(
                    media=callback.message.video.file_id,
                    caption=error_text,
                    parse_mode="HTML"
                )
                await callback.message.edit_media(media=media)
            else:
                await callback.message.edit_text(error_text, parse_mode="HTML")
            return
        
        # Показуємо опції публікації
        options_text = """📤 <b>Оберіть спосіб публікації:</b>

🤖 <b>В бот</b> - збереження авто в базі даних бота
👥 <b>В групу</b> - публікація в Telegram групу
🚀 <b>В бот та групу</b> - одночасна публікація в обох місцях

Оберіть потрібну опцію:"""
        
        if callback.message.photo:
            from aiogram.types import InputMediaPhoto
            media = InputMediaPhoto(
                media=callback.message.photo[-1].file_id,
                caption=options_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(
                media=media,
                reply_markup=get_publication_options_keyboard()
            )
        elif callback.message.video:
            from aiogram.types import InputMediaVideo
            media = InputMediaVideo(
                media=callback.message.video.file_id,
                caption=options_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(
                media=media,
                reply_markup=get_publication_options_keyboard()
            )
        else:
            await callback.message.edit_text(
                options_text,
                reply_markup=get_publication_options_keyboard(),
                parse_mode="HTML"
            )
        
        logger.info(f"📤 Показано опції публікації для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка показу опцій публікації: {e}")
        await callback.answer("❌ Помилка показу опцій", show_alert=True)


@router.callback_query(F.data == "back_to_summary_card")
async def back_to_summary_card(callback: CallbackQuery, state: FSMContext):
    """Повернутися до підсумкової картки"""
    await callback.answer()
    
    try:
        # Отримуємо дані
        data = await state.get_data()
        
        # Форматуємо текст підсумкової картки
        summary_text = format_vehicle_summary(data)
        
        if callback.message.photo:
            from aiogram.types import InputMediaPhoto
            media = InputMediaPhoto(
                media=callback.message.photo[-1].file_id,
                caption=summary_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(
                media=media,
                reply_markup=get_summary_card_keyboard()
            )
        elif callback.message.video:
            from aiogram.types import InputMediaVideo
            media = InputMediaVideo(
                media=callback.message.video.file_id,
                caption=summary_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(
                media=media,
                reply_markup=get_summary_card_keyboard()
            )
        else:
            await callback.message.edit_text(
                summary_text,
                reply_markup=get_summary_card_keyboard(),
                parse_mode="HTML"
            )
        
        logger.info(f"🔙 Повернуто до підсумкової картки для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка повернення до підсумкової картки: {e}")
        await callback.answer("❌ Помилка повернення", show_alert=True)


@router.callback_query(F.data == "publish_to_bot_only")
async def publish_to_bot_only(callback: CallbackQuery, state: FSMContext):
    """Публікація тільки в бот"""
    await callback.answer()
    
    try:
        from ..publication.bot_publisher import create_bot_publisher
        from app.modules.database.manager import DatabaseManager
        
        # Отримуємо дані
        data = await state.get_data()
        
        # Створюємо публікатор
        db_manager = DatabaseManager()
        bot_publisher = await create_bot_publisher(callback.bot, db_manager)
        
        # Підготуємо дані для збереження у БД
        prepared_data = dict(data)
        main_photo = data.get('main_photo')
        group_photos = data.get('group_photos', [])
        prepared_data['main_photo'] = main_photo
        prepared_data['photos'] = group_photos  # Для БД зберігаємо тільки фото групи
        
        # Публікуємо в бот
        success, message, vehicle_id = await bot_publisher.publish_vehicle_to_bot(
            prepared_data, callback.from_user.id
        )
        
        if success:
            result_text = f"✅ <b>АВТО УСПІШНО ЗБЕРЕЖЕНО В БОТ</b>\n\n{message}"
            
            # Перевіряємо підписки та надсилаємо сповіщення
            try:
                from app.modules.client.services.vehicle_search.subscriptions.notifications import check_and_notify_subscriptions
                await check_and_notify_subscriptions(callback.bot, vehicle_id)
            except Exception as e:
                logger.error(f"❌ Помилка перевірки підписок: {e}")
            
            # Очищуємо FSM стан
            await state.clear()
            
            # Перенаправляємо до Управління авто
            await redirect_to_vehicle_management(callback)
        else:
            result_text = f"❌ <b>ПОМИЛКА ЗБЕРЕЖЕННЯ В БОТ</b>\n\n{message}"
        
        # Оновлюємо повідомлення
        if callback.message.photo:
            from aiogram.types import InputMediaPhoto
            media = InputMediaPhoto(
                media=callback.message.photo[-1].file_id,
                caption=result_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(media=media)
        elif callback.message.video:
            from aiogram.types import InputMediaVideo
            media = InputMediaVideo(
                media=callback.message.video.file_id,
                caption=result_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(media=media)
        else:
            await callback.message.edit_text(result_text, parse_mode="HTML")
        
        logger.info(f"🤖 Публікація в бот: success={success} для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка публікації в бот: {e}")
        await callback.answer("❌ Помилка публікації в бот", show_alert=True)


@router.callback_query(F.data == "publish_to_group_only")
async def publish_to_group_only(callback: CallbackQuery, state: FSMContext):
    """Публікація тільки в групу"""
    await callback.answer()
    
    try:
        from ..publication.group_publisher import create_group_publisher
        
        # Отримуємо дані
        data = await state.get_data()
        
        # Підставляємо photos з group_photos (для групи вони і використовуються)
        prepared_data = dict(data)
        prepared_data['photos'] = data.get('group_photos', [])
        
        # Створюємо публікатор
        group_publisher = await create_group_publisher(callback.bot)
        
        # Публікуємо в групу
        success, message, group_message_id = await group_publisher.publish_vehicle_to_group(prepared_data)
        
        if success:
            # Зберігаємо авто в БД з інформацією про публікацію в групу
            from app.modules.database.manager import DatabaseManager
            
            # Підготовка даних для БД
            from ..publication.bot_publisher import BotPublisher
            db_manager = DatabaseManager()
            bot_publisher = BotPublisher(callback.bot, db_manager)
            # Для збереження: окремо main_photo та photos для групи
            save_data = dict(data)
            save_data['main_photo'] = data.get('main_photo')
            save_data['photos'] = data.get('group_photos', [])
            vehicle_model = bot_publisher._prepare_vehicle_model(save_data, callback.from_user.id)
            
            # Встановлюємо дані про публікацію в групу
            vehicle_model.published_in_group = True
            vehicle_model.group_message_id = group_message_id
            
            # Зберігаємо в БД
            vehicle_id = await db_manager.create_vehicle(vehicle_model)
            
            if vehicle_id:
                result_text = f"✅ <b>АВТО УСПІШНО ОПУБЛІКОВАНО В ГРУПУ</b>\n\n{message}\n\n📋 ID авто: {vehicle_id}"
                
                # Перевіряємо підписки та надсилаємо сповіщення
                try:
                    from app.modules.client.services.vehicle_search.subscriptions.notifications import check_and_notify_subscriptions
                    await check_and_notify_subscriptions(callback.bot, vehicle_id)
                except Exception as e:
                    logger.error(f"❌ Помилка перевірки підписок: {e}")
                
                # Очищуємо FSM стан
                await state.clear()
                
                # Перенаправляємо до Управління авто
                await redirect_to_vehicle_management(callback)
            else:
                result_text = f"⚠️ <b>ЧАСТКОВО УСПІШНО</b>\n\n✅ Група: {message}\n❌ БД: Не вдалося зберегти авто в базу даних"
        else:
            result_text = f"❌ <b>ПОМИЛКА ПУБЛІКАЦІЇ В ГРУПУ</b>\n\n{message}"
        
        # Оновлюємо повідомлення
        if callback.message.photo:
            from aiogram.types import InputMediaPhoto
            media = InputMediaPhoto(
                media=callback.message.photo[-1].file_id,
                caption=result_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(media=media)
        elif callback.message.video:
            from aiogram.types import InputMediaVideo
            media = InputMediaVideo(
                media=callback.message.video.file_id,
                caption=result_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(media=media)
        else:
            await callback.message.edit_text(result_text, parse_mode="HTML")
        
        logger.info(f"👥 Публікація в групу: success={success} для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка публікації в групу: {e}")
        await callback.answer("❌ Помилка публікації в групу", show_alert=True)


@router.callback_query(F.data == "publish_to_both")
async def publish_to_both(callback: CallbackQuery, state: FSMContext):
    """Публікація в бот та групу"""
    await callback.answer()
    
    try:
        from ..publication.bot_publisher import create_bot_publisher
        from ..publication.group_publisher import create_group_publisher
        from app.modules.database.manager import DatabaseManager
        
        # Отримуємо дані
        data = await state.get_data()
        
        # Для обох: передаємо main_photo окремо та photos для групи
        data_for_bot = dict(data)
        data_for_bot['main_photo'] = data.get('main_photo')
        data_for_bot['photos'] = data.get('group_photos', [])
        
        # Створюємо публікатори
        db_manager = DatabaseManager()
        bot_publisher = await create_bot_publisher(callback.bot, db_manager)
        group_publisher = await create_group_publisher(callback.bot)
        
        # Публікуємо в бот
        bot_success, bot_message, vehicle_id = await bot_publisher.publish_vehicle_to_bot(
            data_for_bot, callback.from_user.id
        )
        
        # Публікуємо в групу
        data_for_group = dict(data)
        data_for_group['photos'] = data.get('group_photos', [])
        group_success, group_message, group_message_id = await group_publisher.publish_vehicle_to_group(data_for_group)
        
        # Формуємо результат
        if bot_success and group_success:
            # Оновлюємо авто в БД з інформацією про публікацію в групу
            if vehicle_id and group_message_id:
                await db_manager.update_vehicle(vehicle_id, {
                    'published_in_group': True,
                    'group_message_id': group_message_id
                })
            
            # Перевіряємо підписки та надсилаємо сповіщення
            try:
                from app.modules.client.services.vehicle_search.subscriptions.notifications import check_and_notify_subscriptions
                await check_and_notify_subscriptions(callback.bot, vehicle_id)
            except Exception as e:
                logger.error(f"❌ Помилка перевірки підписок: {e}")
            
            result_text = f"✅ <b>АВТО УСПІШНО ОПУБЛІКОВАНО В БОТ ТА ГРУПУ</b>\n\n🤖 Бот: {bot_message}\n👥 Група: {group_message}"
            
            # Очищуємо FSM стан
            await state.clear()
            
            # Перенаправляємо до Управління авто
            await redirect_to_vehicle_management(callback)
        elif bot_success:
            result_text = f"⚠️ <b>ЧАСТКОВО УСПІШНО</b>\n\n✅ Бот: {bot_message}\n❌ Група: {group_message}"
        elif group_success:
            result_text = f"⚠️ <b>ЧАСТКОВО УСПІШНО</b>\n\n❌ Бот: {bot_message}\n✅ Група: {group_message}"
        else:
            result_text = f"❌ <b>ПОМИЛКИ ПУБЛІКАЦІЇ</b>\n\n❌ Бот: {bot_message}\n❌ Група: {group_message}"
        
        # Оновлюємо повідомлення
        if callback.message.photo:
            from aiogram.types import InputMediaPhoto
            media = InputMediaPhoto(
                media=callback.message.photo[-1].file_id,
                caption=result_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(media=media)
        elif callback.message.video:
            from aiogram.types import InputMediaVideo
            media = InputMediaVideo(
                media=callback.message.video.file_id,
                caption=result_text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(media=media)
        else:
            await callback.message.edit_text(result_text, parse_mode="HTML")
        
        logger.info(f"🚀 Публікація в обох: bot={bot_success}, group={group_success} для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка публікації в обох: {e}")
        await callback.answer("❌ Помилка публікації", show_alert=True)


async def redirect_to_vehicle_management(callback: CallbackQuery):
    """Перенаправлення до Управління авто"""
    try:
        from app.modules.admin.shared.modules.keyboards.main_keyboards import get_admin_vehicles_keyboard
        
        vehicles_text = """🚛 <b>Управління авто</b>

<b>Доступні дії:</b>
• ➕ <b>Додати авто</b> - створити нове оголошення
• 📋 <b>Список авто</b> - переглянути всі авто
• 🔍 <b>Пошук авто</b> - знайти конкретне авто
• 📊 <b>Статистика авто</b> - аналітика по авто
• ⚙️ <b>Налаштування</b> - конфігурація авто

Оберіть дію:"""
        
        await callback.message.answer(
            vehicles_text,
            reply_markup=get_admin_vehicles_keyboard(),
            parse_mode="HTML"
        )
        
        logger.info(f"🔄 Перенаправлено до Управління авто користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка перенаправлення: {e}")




@router.callback_query(F.data == "cancel_vehicle_creation")
async def cancel_vehicle_creation(callback: CallbackQuery, state: FSMContext):
    """Скасування створення картки авто"""
    await callback.answer()
    
    # Очищуємо стан
    await state.clear()
    
    # Повертаємося до меню управління авто
    from app.modules.admin.shared.modules.keyboards.main_keyboards import get_admin_vehicles_keyboard
    
    await callback.message.answer(
        "🚛 <b>Управління авто</b>\n\nОберіть дію:",
        reply_markup=get_admin_vehicles_keyboard(),
        parse_mode="HTML"
    )
    
    logger.info(f"📷 Скасовано створення картки авто для користувача {callback.from_user.id}")
