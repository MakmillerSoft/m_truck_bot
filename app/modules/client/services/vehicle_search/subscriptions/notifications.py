"""
Система сповіщень для підписок
"""
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.utils.formatting import get_default_parse_mode
from app.modules.database.manager import db_manager

logger = logging.getLogger(__name__)


async def check_and_notify_subscriptions(bot: Bot, vehicle_id: int):
    """
    Перевірити активні підписки та надіслати сповіщення про нове авто
    
    Args:
        bot: Екземпляр бота
        vehicle_id: ID нового авто
    """
    try:
        # Отримуємо авто
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            logger.warning(f"⚠️ Авто {vehicle_id} не знайдено для сповіщень підписок")
            return
        
        # Отримуємо всі активні підписки
        subscriptions = await db_manager.get_active_subscriptions()
        
        if not subscriptions:
            logger.info("ℹ️ Немає активних підписок для перевірки")
            return
        
        logger.info(f"📊 Перевіряємо {len(subscriptions)} активних підписок для авто {vehicle_id}")
        
        # Перевіряємо кожну підписку
        notified_count = 0
        for subscription in subscriptions:
            # Перевіряємо чи авто відповідає критеріям підписки
            if _matches_subscription(vehicle, subscription):
                # Надсилаємо сповіщення користувачу
                success = await _send_subscription_notification(bot, subscription, vehicle)
                if success:
                    notified_count += 1
                    # Оновлюємо час останнього сповіщення
                    await db_manager.update_subscription_last_notification(subscription['id'])
        
        logger.info(f"✅ Надіслано {notified_count} сповіщень про нове авто {vehicle_id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка перевірки підписок: {e}", exc_info=True)


def _matches_subscription(vehicle, subscription: dict) -> bool:
    """
    Перевірити чи авто відповідає критеріям підписки
    
    Args:
        vehicle: Об'єкт авто
        subscription: Словник з параметрами підписки
    
    Returns:
        True якщо авто відповідає критеріям
    """
    logger.info(f"🔍 Перевірка авто {vehicle.id} для підписки {subscription.get('id')}")
    logger.info(f"   Авто: type={vehicle.vehicle_type}, brand={vehicle.brand}, year={vehicle.year}, price={vehicle.price}, condition={vehicle.condition}")
    logger.info(f"   Підписка: type={subscription.get('vehicle_type')}, brand={subscription.get('brand')}, year={subscription.get('min_year')}-{subscription.get('max_year')}, price={subscription.get('min_price')}-{subscription.get('max_price')}, condition={subscription.get('condition')}")
    
    # Мапінг українських назв на англійські
    VEHICLE_TYPE_MAPPING_UA_TO_EN = {
        "Контейнеровози": "container_carrier",
        "Напівпричепи контейнеровози": "semi_container_carrier",
        "Змінні кузови": "variable_body",
        "Сідельні тягачі": "saddle_tractor",
        "Причіпи": "trailer",
        "Рефрижератори": "refrigerator",
        "Фургони": "van",
        "Буси": "bus",
    }
    
    # Перевіряємо тип авто
    if subscription.get('vehicle_type'):
        # Конвертуємо українське значення авто в англійське для порівняння
        vehicle_type_en = VEHICLE_TYPE_MAPPING_UA_TO_EN.get(vehicle.vehicle_type, vehicle.vehicle_type)
        logger.info(f"   Порівняння типу: {vehicle_type_en} == {subscription['vehicle_type']}")
        if vehicle_type_en != subscription['vehicle_type']:
            logger.info(f"   ❌ Тип не співпадає")
            return False
    
    # Перевіряємо бренд
    if subscription.get('brand'):
        logger.info(f"   Порівняння бренду: {vehicle.brand.lower()} == {subscription['brand'].lower()}")
        if vehicle.brand.lower() != subscription['brand'].lower():
            logger.info(f"   ❌ Бренд не співпадає")
            return False
    
    # Перевіряємо мінімальний рік
    if subscription.get('min_year'):
        logger.info(f"   Порівняння мін. року: {vehicle.year} >= {subscription['min_year']}")
        if vehicle.year < subscription['min_year']:
            logger.info(f"   ❌ Рік менше мінімального")
            return False
    
    # Перевіряємо максимальний рік
    if subscription.get('max_year'):
        logger.info(f"   Порівняння макс. року: {vehicle.year} <= {subscription['max_year']}")
        if vehicle.year > subscription['max_year']:
            logger.info(f"   ❌ Рік більше максимального")
            return False
    
    # Перевіряємо мінімальну ціну
    if subscription.get('min_price'):
        logger.info(f"   Порівняння мін. ціни: {vehicle.price} >= {subscription['min_price']}")
        if vehicle.price < subscription['min_price']:
            logger.info(f"   ❌ Ціна менше мінімальної")
            return False
    
    # Перевіряємо максимальну ціну
    if subscription.get('max_price'):
        logger.info(f"   Порівняння макс. ціни: {vehicle.price} <= {subscription['max_price']}")
        if vehicle.price > subscription['max_price']:
            logger.info(f"   ❌ Ціна більше максимальної")
            return False
    
    # Перевіряємо максимальний пробіг
    if subscription.get('max_mileage'):
        logger.info(f"   Порівняння пробігу: {vehicle.mileage} <= {subscription['max_mileage']}")
        if vehicle.mileage and vehicle.mileage > subscription['max_mileage']:
            logger.info(f"   ❌ Пробіг більше максимального")
            return False
    
    # Перевіряємо стан (може бути "used" або "Вживане")
    if subscription.get('condition'):
        # Мапінг для стану
        condition_mapping_ua_to_en = {
            "Новий": "new",
            "Вживане": "used",
        }
        vehicle_condition_en = condition_mapping_ua_to_en.get(vehicle.condition, vehicle.condition)
        logger.info(f"   Порівняння стану: {vehicle_condition_en} == {subscription['condition']}")
        if vehicle_condition_en != subscription['condition']:
            logger.info(f"   ❌ Стан не співпадає")
            return False
    
    logger.info(f"   ✅ Авто відповідає всім критеріям підписки!")
    return True


async def _send_subscription_notification(bot: Bot, subscription: dict, vehicle) -> bool:
    """
    Надіслати сповіщення користувачу про нове авто
    
    Args:
        bot: Екземпляр бота
        subscription: Словник з даними підписки
        vehicle: Об'єкт авто
    
    Returns:
        True якщо сповіщення надіслано успішно
    """
    try:
        # Отримуємо користувача
        user_id = subscription.get('user_id')
        if not user_id:
            logger.warning(f"⚠️ Підписка {subscription.get('id')} без user_id")
            return False
        
        # Отримуємо telegram_id користувача через БД
        import aiosqlite
        
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT telegram_id FROM users WHERE id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    logger.warning(f"⚠️ Користувач {user_id} не знайдений")
                    return False
                
                telegram_id = row['telegram_id']
        
        # Мапінг для читабельного відображення типу авто
        vehicle_type_display = {
            "VehicleType.CONTAINER_CARRIER": "Контейнеровоз",
            "VehicleType.SEMI_CONTAINER_CARRIER": "Напівпричіп контейнеровоз",
            "VehicleType.VARIABLE_BODY": "Змінний кузов",
            "VehicleType.SADDLE_TRACTOR": "Сідельний тягач",
            "VehicleType.TRAILER": "Причіп",
            "VehicleType.REFRIGERATOR": "Рефрижератор",
            "VehicleType.VAN": "Фургон",
            "VehicleType.BUS": "Бус",
        }
        
        # Мапінг для читабельного відображення стану
        condition_display = {
            "VehicleCondition.NEW": "Новий",
            "VehicleCondition.USED": "Вживане",
        }
        
        # Отримуємо читабельні значення
        vehicle_type_str = vehicle_type_display.get(str(vehicle.vehicle_type), vehicle.vehicle_type)
        condition_str = condition_display.get(str(vehicle.condition), vehicle.condition)
        
        # Формуємо повідомлення
        text = f"""
🔔 <b>Нове авто за вашою підпискою!</b>

📝 <b>Підписка:</b> {subscription.get('subscription_name', 'Без назви')}

🚛 <b>Авто:</b>
• <b>Бренд:</b> {vehicle.brand}
• <b>Модель:</b> {vehicle.model}
• <b>Рік:</b> {vehicle.year}
• <b>Ціна:</b> ${vehicle.price:,.0f}
• <b>Тип:</b> {vehicle_type_str}
• <b>Стан:</b> {condition_str}
"""
        
        if vehicle.mileage:
            text += f"• <b>Пробіг:</b> {vehicle.mileage:,} км\n"
        
        text += "\n<i>Натисніть кнопку нижче, щоб переглянути це авто!</i>"
        
        # Створюємо клавіатуру з прямим посиланням на авто
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="🚛 Переглянути авто",
                    callback_data=f"client_view_vehicle_{vehicle.id}"
                )],
                [InlineKeyboardButton(
                    text="🔔 Мої підписки",
                    callback_data="client_subscriptions"
                )]
            ]
        )
        
        # Надсилаємо повідомлення
        await bot.send_message(
            chat_id=telegram_id,
            text=text.strip(),
            reply_markup=keyboard,
            parse_mode=get_default_parse_mode(),
        )
        
        logger.info(f"✅ Сповіщення надіслано користувачу {telegram_id} про авто {vehicle.id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Помилка надсилання сповіщення: {e}", exc_info=True)
        return False

