"""
Статистика авто для адмін панелі
"""
import logging
from typing import Dict, List, Tuple
from collections import Counter

from app.modules.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

# Ініціалізуємо менеджер бази даних
db_manager = DatabaseManager()


async def get_vehicles_statistics() -> Dict:
    """Отримати загальну статистику по авто"""
    try:
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Отримуємо загальну кількість авто
            async with db.execute("SELECT COUNT(*) as count FROM vehicles WHERE is_active = 1") as cursor:
                total_vehicles = (await cursor.fetchone())['count']
            
            # Отримуємо кількість унікальних марок
            async with db.execute("SELECT COUNT(DISTINCT brand) as count FROM vehicles WHERE is_active = 1 AND brand IS NOT NULL") as cursor:
                total_brands = (await cursor.fetchone())['count']
            
            # Отримуємо топ марок
            async with db.execute("""
                SELECT brand, COUNT(*) as count 
                FROM vehicles 
                WHERE is_active = 1 AND brand IS NOT NULL 
                GROUP BY brand 
                ORDER BY count DESC 
                LIMIT 10
            """) as cursor:
                top_brands = [(row['brand'], row['count']) for row in await cursor.fetchall()]
            
            # Розраховуємо кількість сторінок (10 авто на сторінку)
            total_pages = (total_vehicles + 9) // 10  # Округлення вгору
            
            return {
                'total_vehicles': total_vehicles,
                'total_brands': total_brands,
                'top_brands': top_brands,
                'total_pages': total_pages
            }
            
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики авто: {e}")
        return {
            'total_vehicles': 0,
            'total_brands': 0,
            'top_brands': [],
            'total_pages': 1
        }


async def get_detailed_statistics() -> Dict:
    """Отримати детальну статистику по авто"""
    try:
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Загальна статистика
            basic_stats = await get_vehicles_statistics()
            
            # Статистика по типах авто
            async with db.execute("""
                SELECT vehicle_type, COUNT(*) as count 
                FROM vehicles 
                WHERE is_active = 1 
                GROUP BY vehicle_type 
                ORDER BY count DESC
            """) as cursor:
                type_stats = {}
                async for row in cursor:
                    type_stats[row['vehicle_type']] = row['count']
            
            # Статистика по станах
            async with db.execute("""
                SELECT condition, COUNT(*) as count 
                FROM vehicles 
                WHERE is_active = 1 AND condition IS NOT NULL 
                GROUP BY condition 
                ORDER BY count DESC
            """) as cursor:
                condition_stats = {}
                async for row in cursor:
                    condition_stats[row['condition']] = row['count']
            
            # Статистика по цінах
            async with db.execute("""
                SELECT 
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(price) as avg_price,
                    COUNT(price) as count_with_price
                FROM vehicles 
                WHERE is_active = 1 AND price IS NOT NULL AND price > 0
            """) as cursor:
                row = await cursor.fetchone()
                price_stats = {
                    'min_price': row['min_price'] or 0,
                    'max_price': row['max_price'] or 0,
                    'avg_price': row['avg_price'] or 0,
                    'count_with_price': row['count_with_price'] or 0
                }
            
            # Статистика по роках
            async with db.execute("""
                SELECT 
                    MIN(year) as min_year,
                    MAX(year) as max_year,
                    AVG(year) as avg_year,
                    COUNT(year) as count_with_year
                FROM vehicles 
                WHERE is_active = 1 AND year IS NOT NULL AND year > 1900
            """) as cursor:
                row = await cursor.fetchone()
                year_stats = {
                    'min_year': row['min_year'] or 0,
                    'max_year': row['max_year'] or 0,
                    'avg_year': row['avg_year'] or 0,
                    'count_with_year': row['count_with_year'] or 0
                }
            
            # Статистика публікацій
            async with db.execute("""
                SELECT 
                    COUNT(CASE WHEN published_in_group = 1 THEN 1 END) as published_in_group,
                    COUNT(CASE WHEN published_in_bot = 1 THEN 1 END) as published_in_bot,
                    COUNT(CASE WHEN published_in_group = 1 OR published_in_bot = 1 THEN 1 END) as total_published,
                    COUNT(CASE WHEN published_in_group = 0 AND published_in_bot = 0 THEN 1 END) as not_published
                FROM vehicles 
                WHERE is_active = 1
            """) as cursor:
                row = await cursor.fetchone()
                publication_stats = {
                    'published_in_group': row['published_in_group'] or 0,
                    'published_in_bot': row['published_in_bot'] or 0,
                    'total_published': row['total_published'] or 0,
                    'not_published': row['not_published'] or 0
                }
            
            return {
                **basic_stats,
                'type_stats': type_stats,
                'condition_stats': condition_stats,
                'price_stats': price_stats,
                'year_stats': year_stats,
                'publication_stats': publication_stats
            }
            
    except Exception as e:
        logger.error(f"❌ Помилка отримання детальної статистики: {e}")
        return await get_vehicles_statistics()


async def get_brand_statistics() -> Dict[str, int]:
    """Отримати статистику по марках"""
    try:
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute("""
                SELECT brand, COUNT(*) as count 
                FROM vehicles 
                WHERE is_active = 1 AND brand IS NOT NULL 
                GROUP BY brand 
                ORDER BY count DESC
            """) as cursor:
                brand_stats = {}
                async for row in cursor:
                    brand_stats[row['brand']] = row['count']
                
                return brand_stats
                
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики марок: {e}")
        return {}


async def get_vehicle_type_statistics() -> Dict[str, int]:
    """Отримати статистику по типах авто"""
    try:
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute("""
                SELECT vehicle_type, COUNT(*) as count 
                FROM vehicles 
                WHERE is_active = 1 
                GROUP BY vehicle_type 
                ORDER BY count DESC
            """) as cursor:
                type_stats = {}
                async for row in cursor:
                    type_stats[row['vehicle_type']] = row['count']
                
                return type_stats
                
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики типів авто: {e}")
        return {}


async def get_price_statistics() -> Dict[str, float]:
    """Отримати статистику по цінах"""
    try:
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute("""
                SELECT 
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(price) as avg_price,
                    COUNT(price) as count_with_price
                FROM vehicles 
                WHERE is_active = 1 AND price IS NOT NULL AND price > 0
            """) as cursor:
                row = await cursor.fetchone()
                
                return {
                    'min_price': row['min_price'] or 0,
                    'max_price': row['max_price'] or 0,
                    'avg_price': row['avg_price'] or 0,
                    'count_with_price': row['count_with_price'] or 0
                }
                
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики цін: {e}")
        return {
            'min_price': 0,
            'max_price': 0,
            'avg_price': 0,
            'count_with_price': 0
        }


async def get_monthly_statistics() -> Dict[str, int]:
    """Отримати статистику по місяцях (останні 12 місяців)"""
    try:
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute("""
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    COUNT(*) as count
                FROM vehicles 
                WHERE is_active = 1 
                AND created_at >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month DESC
            """) as cursor:
                monthly_stats = {}
                async for row in cursor:
                    monthly_stats[row['month']] = row['count']
                
                return monthly_stats
                
    except Exception as e:
        logger.error(f"❌ Помилка отримання місячної статистики: {e}")
        return {}


async def get_top_performers() -> Dict[str, List[Tuple[str, int]]]:
    """Отримати топ-виконавців по різних категоріях"""
    try:
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Топ марки
            async with db.execute("""
                SELECT brand, COUNT(*) as count 
                FROM vehicles 
                WHERE is_active = 1 AND brand IS NOT NULL 
                GROUP BY brand 
                ORDER BY count DESC 
                LIMIT 5
            """) as cursor:
                top_brands = [(row['brand'], row['count']) for row in await cursor.fetchall()]
            
            # Топ типи авто
            async with db.execute("""
                SELECT vehicle_type, COUNT(*) as count 
                FROM vehicles 
                WHERE is_active = 1 
                GROUP BY vehicle_type 
                ORDER BY count DESC 
                LIMIT 5
            """) as cursor:
                top_types = [(row['vehicle_type'], row['count']) for row in await cursor.fetchall()]
            
            # Топ роки
            async with db.execute("""
                SELECT year, COUNT(*) as count 
                FROM vehicles 
                WHERE is_active = 1 AND year IS NOT NULL 
                GROUP BY year 
                ORDER BY count DESC 
                LIMIT 5
            """) as cursor:
                top_years = [(str(row['year']), row['count']) for row in await cursor.fetchall()]
            
            return {
                'top_brands': top_brands,
                'top_types': top_types,
                'top_years': top_years
            }
                
    except Exception as e:
        logger.error(f"❌ Помилка отримання топ-виконавців: {e}")
        return {
            'top_brands': [],
            'top_types': [],
            'top_years': []
        }
