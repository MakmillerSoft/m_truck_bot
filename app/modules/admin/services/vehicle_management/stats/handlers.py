"""
Обробники для модуля статистики авто
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from .statistics import (
    get_vehicles_statistics,
    get_detailed_statistics,
    get_brand_statistics,
    get_vehicle_type_statistics,
    get_price_statistics,
    get_monthly_statistics,
    get_top_performers
)
from .keyboards import (
    get_stats_main_keyboard,
    get_detailed_stats_keyboard,
    get_brand_stats_keyboard,
    get_price_stats_keyboard,
    get_monthly_stats_keyboard
)
from ..shared.translations import translate_field_value

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())


@router.callback_query(F.data == "admin_vehicle_stats")
async def show_vehicle_stats(callback: CallbackQuery, state: FSMContext):
    """Показати головну статистику авто"""
    await callback.answer()
    
    try:
        # Отримуємо базову статистику
        stats = await get_vehicles_statistics()
        
        # Форматуємо текст статистики
        stats_text = f"""📊 <b>Статистика авто</b>

📈 <b>Загальна статистика:</b>
• 🚛 <b>Всього авто:</b> {stats['total_vehicles']}
• 🏷️ <b>Марок:</b> {stats['total_brands']}
• 📄 <b>Сторінок:</b> {stats['total_pages']}

🏭 <b>Топ-5 марок:</b>
"""
        
        # Додаємо топ-5 марок
        for i, (brand, count) in enumerate(stats['top_brands'][:5], 1):
            stats_text += f"{i}. <b>{brand}</b> - {count} авто\n"
        
        stats_text += "\n📊 <b>Оберіть тип статистики для детального перегляду:</b>"
        
        # Відправляємо статистику
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_stats_main_keyboard(),
            parse_mode="HTML"
        )
        
        logger.info(f"📊 Показано статистику авто для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження статистики: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка завантаження статистики</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "detailed_stats")
async def show_detailed_stats(callback: CallbackQuery, state: FSMContext):
    """Показати детальну статистику"""
    await callback.answer()
    
    try:
        # Отримуємо детальну статистику
        stats = await get_detailed_statistics()
        
        # Форматуємо детальну статистику
        stats_text = f"""📊 <b>Детальна статистика авто</b>

📈 <b>Загальна інформація:</b>
• 🚛 <b>Всього авто:</b> {stats['total_vehicles']}
• 🏷️ <b>Марок:</b> {stats['total_brands']}

📦 <b>Статистика по типах авто:</b>
"""
        
        # Додаємо статистику по типах
        for vehicle_type, count in stats['type_stats'].items():
            translated_type = translate_field_value('vehicle_type', vehicle_type)
            stats_text += f"• <b>{translated_type}:</b> {count} авто\n"
        
        stats_text += "\n⭐ <b>Статистика по станах:</b>\n"
        
        # Додаємо статистику по станах
        for condition, count in stats['condition_stats'].items():
            translated_condition = translate_field_value('condition', condition)
            stats_text += f"• <b>{translated_condition}:</b> {count} авто\n"
        
        stats_text += "\n💰 <b>Статистика по цінах:</b>\n"
        price_stats = stats['price_stats']
        if price_stats['count_with_price'] > 0:
            stats_text += f"• <b>Мінімальна ціна:</b> {price_stats['min_price']:,.0f} $\n"
            stats_text += f"• <b>Максимальна ціна:</b> {price_stats['max_price']:,.0f} $\n"
            stats_text += f"• <b>Середня ціна:</b> {price_stats['avg_price']:,.0f} $\n"
            stats_text += f"• <b>З вказаною ціною:</b> {price_stats['count_with_price']} авто\n"
        else:
            stats_text += "• Ціни не вказані\n"
        
        stats_text += "\n📅 <b>Статистика по роках:</b>\n"
        year_stats = stats['year_stats']
        if year_stats['count_with_year'] > 0:
            stats_text += f"• <b>Найстаріший:</b> {year_stats['min_year']} рік\n"
            stats_text += f"• <b>Найновіший:</b> {year_stats['max_year']} рік\n"
            stats_text += f"• <b>Середній рік:</b> {year_stats['avg_year']:.0f}\n"
            stats_text += f"• <b>З вказаним роком:</b> {year_stats['count_with_year']} авто\n"
        else:
            stats_text += "• Роки не вказані\n"
        
        stats_text += "\n📤 <b>Статистика публікацій:</b>\n"
        pub_stats = stats['publication_stats']
        stats_text += f"• <b>Опубліковано в групу:</b> {pub_stats['published_in_group']} авто\n"
        stats_text += f"• <b>Опубліковано в бот:</b> {pub_stats['published_in_bot']} авто\n"
        stats_text += f"• <b>Всього опубліковано:</b> {pub_stats['total_published']} авто\n"
        stats_text += f"• <b>Не опубліковано:</b> {pub_stats['not_published']} авто\n"
        
        # Відправляємо детальну статистику
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_detailed_stats_keyboard(),
            parse_mode="HTML"
        )
        
        logger.info(f"📊 Показано детальну статистику для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження детальної статистики: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка завантаження детальної статистики</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "brand_stats")
async def show_brand_stats(callback: CallbackQuery, state: FSMContext):
    """Показати статистику по марках"""
    await callback.answer()
    
    try:
        # Отримуємо статистику по марках
        brand_stats = await get_brand_statistics()
        
        if not brand_stats:
            await callback.message.edit_text(
                "📊 <b>Статистика по марках</b>\n\n❌ Дані не знайдені",
                parse_mode="HTML"
            )
            return
        
        # Форматуємо статистику по марках
        stats_text = "📊 <b>Статистика по марках авто</b>\n\n"
        
        # Сортуємо марки за кількістю авто
        sorted_brands = sorted(brand_stats.items(), key=lambda x: x[1], reverse=True)
        
        for i, (brand, count) in enumerate(sorted_brands, 1):
            stats_text += f"{i}. <b>{brand}</b> - {count} авто\n"
        
        # Відправляємо статистику по марках
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_brand_stats_keyboard(),
            parse_mode="HTML"
        )
        
        logger.info(f"📊 Показано статистику по марках для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження статистики марок: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка завантаження статистики марок</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "price_stats")
async def show_price_stats(callback: CallbackQuery, state: FSMContext):
    """Показати статистику по цінах"""
    await callback.answer()
    
    try:
        # Отримуємо статистику по цінах
        price_stats = await get_price_statistics()
        
        # Форматуємо статистику по цінах
        stats_text = "📊 <b>Статистика по цінах авто</b>\n\n"
        
        if price_stats['count_with_price'] > 0:
            stats_text += f"💰 <b>Загальна статистика:</b>\n"
            stats_text += f"• <b>Авто з ціною:</b> {price_stats['count_with_price']}\n"
            stats_text += f"• <b>Мінімальна ціна:</b> {price_stats['min_price']:,.0f} $\n"
            stats_text += f"• <b>Максимальна ціна:</b> {price_stats['max_price']:,.0f} $\n"
            stats_text += f"• <b>Середня ціна:</b> {price_stats['avg_price']:,.0f} $\n"
            
            # Розраховуємо діапазони цін
            price_range = price_stats['max_price'] - price_stats['min_price']
            stats_text += f"• <b>Діапазон цін:</b> {price_range:,.0f} $\n"
            
            # Відсоток авто з ціною
            total_vehicles = await get_vehicles_statistics()
            percentage = (price_stats['count_with_price'] / total_vehicles['total_vehicles']) * 100 if total_vehicles['total_vehicles'] > 0 else 0
            stats_text += f"• <b>Відсоток з ціною:</b> {percentage:.1f}%\n"
        else:
            stats_text += "❌ <b>Немає авто з вказаною ціною</b>\n"
        
        # Відправляємо статистику по цінах
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_price_stats_keyboard(),
            parse_mode="HTML"
        )
        
        logger.info(f"📊 Показано статистику по цінах для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження статистики цін: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка завантаження статистики цін</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "monthly_stats")
async def show_monthly_stats(callback: CallbackQuery, state: FSMContext):
    """Показати місячну статистику"""
    await callback.answer()
    
    try:
        # Отримуємо місячну статистику
        monthly_stats = await get_monthly_statistics()
        
        if not monthly_stats:
            await callback.message.edit_text(
                "📊 <b>Місячна статистика</b>\n\n❌ Дані не знайдені",
                parse_mode="HTML"
            )
            return
        
        # Форматуємо місячну статистику
        stats_text = "📊 <b>Місячна статистика (останні 12 місяців)</b>\n\n"
        
        # Сортуємо місяці за датою (від нових до старих)
        sorted_months = sorted(monthly_stats.items(), key=lambda x: x[0], reverse=True)
        
        for month, count in sorted_months:
            # Форматуємо місяць для кращого відображення
            year, month_num = month.split('-')
            month_names = {
                '01': 'Січень', '02': 'Лютий', '03': 'Березень', '04': 'Квітень',
                '05': 'Травень', '06': 'Червень', '07': 'Липень', '08': 'Серпень',
                '09': 'Вересень', '10': 'Жовтень', '11': 'Листопад', '12': 'Грудень'
            }
            month_name = month_names.get(month_num, month_num)
            stats_text += f"• <b>{month_name} {year}:</b> {count} авто\n"
        
        # Відправляємо місячну статистику
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_monthly_stats_keyboard(),
            parse_mode="HTML"
        )
        
        logger.info(f"📊 Показано місячну статистику для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження місячної статистики: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка завантаження місячної статистики</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "back_to_stats_main")
async def back_to_stats_main(callback: CallbackQuery, state: FSMContext):
    """Повернутися до головної статистики"""
    await callback.answer()
    
    # Повертаємося до головної статистики
    await show_vehicle_stats(callback, state)
