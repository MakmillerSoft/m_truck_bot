"""
Менеджер бази даних
"""

import aiosqlite
import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

from app.config.settings import settings
from .models import (
    UserModel,
    VehicleModel,
    VehicleStatus,
    ListingModel,
    PhotoModel,
    SearchRequestModel,
    SearchHistoryModel,
    SubscriptionModel,
    GroupTopicModel,
    BroadcastModel,
)


class DatabaseManager:
    """Менеджер для роботи з базою даних"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")

    def _process_vehicle_data(self, vehicle_data: dict) -> dict:
        """Обробити дані авто для Pydantic моделі"""
        # Обробляємо JSON поле photos
        if vehicle_data.get('photos'):
            try:
                import json
                vehicle_data['photos'] = json.loads(vehicle_data['photos'])
            except:
                vehicle_data['photos'] = []
        else:
            vehicle_data['photos'] = []
        
        # Обробляємо поле status (якщо відсутнє, встановлюємо за замовчуванням)
        if not vehicle_data.get('status'):
            vehicle_data['status'] = 'available'
        
        # Обробляємо дати статусу
        if vehicle_data.get('status_changed_at'):
            try:
                from datetime import datetime
                vehicle_data['status_changed_at'] = datetime.fromisoformat(vehicle_data['status_changed_at'])
            except:
                vehicle_data['status_changed_at'] = None
        
        if vehicle_data.get('sold_at'):
            try:
                from datetime import datetime
                vehicle_data['sold_at'] = datetime.fromisoformat(vehicle_data['sold_at'])
            except:
                vehicle_data['sold_at'] = None
        
        return vehicle_data

    async def init_database(self):
        """Ініціалізація бази даних та створення таблиць"""
        async with aiosqlite.connect(self.db_path) as db:
            # Створення таблиці користувачів
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    role TEXT NOT NULL DEFAULT 'buyer',
                    is_active BOOLEAN DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Створення таблиці авто
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    status TEXT DEFAULT 'available',
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    mileage INTEGER,
                    engine_volume REAL,
                    power_hp INTEGER,
                    transmission TEXT,
                    fuel_type TEXT,
                    body_type TEXT,
                    wheel_radius TEXT,
                    load_capacity INTEGER,
                    total_weight INTEGER,
                    cargo_dimensions TEXT,
                    location TEXT,
                    description TEXT,
                    photos TEXT DEFAULT '[]',
                    seller_id INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    views_count INTEGER DEFAULT 0,
                    published_at TIMESTAMP,
                    published_in_group BOOLEAN DEFAULT 0,
                    published_in_bot BOOLEAN DEFAULT 0,
                    group_message_id INTEGER,
                    bot_message_id INTEGER,
                    vin_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES users(id)
                )
            """
            )


            # Створення таблиці пошукових запитів
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS search_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    vehicle_type TEXT,
                    brand TEXT,
                    min_year INTEGER,
                    max_year INTEGER,
                    min_price REAL,
                    max_price REAL,
                    max_mileage INTEGER,
                    location TEXT,
                    is_saved BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            # Створення таблиці збережених авто
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    vehicle_id INTEGER NOT NULL,
                    notes TEXT,
                    category TEXT DEFAULT 'favorites',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                    UNIQUE(user_id, vehicle_id)
                )
            """
            )

            # Створення таблиці заявок менеджеру
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS manager_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    vehicle_id INTEGER,
                    request_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
                )
            """
            )

            # Міграція: додати vehicle_id якщо відсутній
            try:
                async with db.execute("PRAGMA table_info(manager_requests)") as cursor:
                    cols = await cursor.fetchall()
                    col_names = {row[1] for row in cols}
                    if "vehicle_id" not in col_names:
                        await db.execute("ALTER TABLE manager_requests ADD COLUMN vehicle_id INTEGER")
                        await db.commit()
                        logger.info("ℹ️ Колонка vehicle_id додана в таблицю manager_requests")
            except Exception as e:
                logger.info(f"ℹ️ Колонка vehicle_id вже існує або помилка: {e}")
            
            # Міграція: додати processed_by_admin_id та processed_at для логування
            try:
                async with db.execute("PRAGMA table_info(manager_requests)") as cursor:
                    cols = await cursor.fetchall()
                    col_names = {row[1] for row in cols}
                    
                    if "processed_by_admin_id" not in col_names:
                        await db.execute("ALTER TABLE manager_requests ADD COLUMN processed_by_admin_id INTEGER")
                        await db.commit()
                        logger.info("ℹ️ Колонка processed_by_admin_id додана в таблицю manager_requests")
                    
                    if "processed_at" not in col_names:
                        await db.execute("ALTER TABLE manager_requests ADD COLUMN processed_at TIMESTAMP")
                        await db.commit()
                        logger.info("ℹ️ Колонка processed_at додана в таблицю manager_requests")
            except Exception as e:
                logger.info(f"ℹ️ Колонки логування вже існують або помилка: {e}")
            
            # Міграція: зробити необов'язкові поля в таблиці vehicles та додати main_photo
            try:
                # Перевіряємо чи потрібна міграція
                async with db.execute("PRAGMA table_info(vehicles)") as cursor:
                    cols = await cursor.fetchall()
                    col_names = {col[1] for col in cols}
                    
                    # Якщо є NOT NULL на brand, model, year, condition, price - робимо міграцію
                    needs_migration = False
                    for col in cols:
                        col_name = col[1]
                        not_null = col[3]  # 0 = NULL allowed, 1 = NOT NULL
                        if col_name in ['brand', 'model', 'year', 'condition', 'price'] and not_null == 1:
                            needs_migration = True
                            break
                    
                    # Перевіряємо чи є поле main_photo
                    needs_main_photo = 'main_photo' not in col_names
                    
                    if needs_migration or needs_main_photo:
                        logger.info("🔄 Починаємо міграцію таблиці vehicles для необов'язкових полів та main_photo...")
                        
                        # Створюємо нову таблицю з правильною схемою
                        await db.execute("""
                            CREATE TABLE IF NOT EXISTS vehicles_new (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                brand TEXT,
                                model TEXT,
                                year INTEGER,
                                vehicle_type TEXT NOT NULL,
                                condition TEXT,
                                status TEXT DEFAULT 'available',
                                price REAL,
                                currency TEXT DEFAULT 'USD',
                                mileage INTEGER,
                                engine_volume REAL,
                                power_hp INTEGER,
                                transmission TEXT,
                                fuel_type TEXT,
                                body_type TEXT,
                                wheel_radius TEXT,
                                load_capacity INTEGER,
                                total_weight INTEGER,
                                cargo_dimensions TEXT,
                                location TEXT,
                                description TEXT,
                                photos TEXT DEFAULT '[]',
                                main_photo TEXT,
                                seller_id INTEGER NOT NULL,
                                is_active BOOLEAN DEFAULT 1,
                                views_count INTEGER DEFAULT 0,
                                published_at TIMESTAMP,
                                published_in_group BOOLEAN DEFAULT 0,
                                published_in_bot BOOLEAN DEFAULT 0,
                                group_message_id INTEGER,
                                bot_message_id INTEGER,
                                vin_code TEXT,
                                status_changed_at TIMESTAMP,
                                sold_at TIMESTAMP,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (seller_id) REFERENCES users(id)
                            )
                        """)
                        
                        # Копіюємо дані зі старої таблиці (додаємо main_photo як NULL)
                        await db.execute("""
                            INSERT INTO vehicles_new 
                            SELECT *, NULL as main_photo FROM vehicles
                        """)
                        
                        # Видаляємо стару таблицю
                        await db.execute("DROP TABLE vehicles")
                        
                        # Перейменовуємо нову таблицю
                        await db.execute("ALTER TABLE vehicles_new RENAME TO vehicles")
                        
                        await db.commit()
                        logger.info("✅ Міграція таблиці vehicles завершена успішно!")
                    else:
                        logger.info("ℹ️ Таблиця vehicles вже має правильну схему")
            except Exception as e:
                logger.error(f"❌ Помилка міграції таблиці vehicles: {e}")

            # Створення таблиці історії пошуків
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    search_name TEXT NOT NULL,
                    vehicle_type TEXT,
                    brand TEXT,
                    min_year INTEGER,
                    max_year INTEGER,
                    min_price REAL,
                    max_price REAL,
                    max_mileage INTEGER,
                    location TEXT,
                    engine_type TEXT,
                    fuel_type TEXT,
                    load_capacity INTEGER,
                    condition TEXT,
                    results_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            # Створення таблиці підписок
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subscription_name TEXT NOT NULL,
                    vehicle_type TEXT,
                    brand TEXT,
                    min_year INTEGER,
                    max_year INTEGER,
                    min_price REAL,
                    max_price REAL,
                    max_mileage INTEGER,
                    location TEXT,
                    engine_type TEXT,
                    fuel_type TEXT,
                    load_capacity INTEGER,
                    condition TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    last_notification TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )

            # Створення таблиць для розсилок та топіків групи
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS group_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    button_text TEXT,
                    button_url TEXT,
                    media_type TEXT,
                    media_file_id TEXT,
                    media_group_id TEXT,
                    status TEXT DEFAULT 'draft', -- draft | sent | scheduled
                    schedule_period TEXT DEFAULT 'none', -- none | daily | weekly
                    scheduled_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS broadcast_deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    broadcast_id INTEGER NOT NULL,
                    topic_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending', -- pending | success | failed
                    sent_at TIMESTAMP,
                    error TEXT,
                    FOREIGN KEY (broadcast_id) REFERENCES broadcasts(id),
                    FOREIGN KEY (topic_id) REFERENCES group_topics(id)
                )
            """
            )

            # Додаємо колонку photos якщо її немає
            try:
                # Перевіряємо, чи існує колонка photos
                cursor = await db.execute("PRAGMA table_info(vehicles)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'photos' not in column_names:
                    await db.execute("ALTER TABLE vehicles ADD COLUMN photos TEXT DEFAULT '[]'")
                    await db.commit()
                    logger.info("✅ Колонка photos додана до таблиці vehicles")
                else:
                    logger.info("ℹ️ Колонка photos вже існує в таблиці vehicles")
                
                # Перевіряємо, чи існує колонка engine_type (видаляємо її)
                if 'engine_type' in column_names:
                    # SQLite не підтримує DROP COLUMN, тому створюємо нову таблицю
                    await db.execute("""
                        CREATE TABLE vehicles_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            brand TEXT,
                            model TEXT,
                            year INTEGER,
                            vehicle_type TEXT NOT NULL,
                            condition TEXT,
                            price REAL,
                            currency TEXT DEFAULT 'USD',
                            mileage INTEGER,
                            engine_volume REAL,
                            power_hp INTEGER,
                            transmission TEXT,
                            fuel_type TEXT,
                            body_type TEXT,
                            wheel_radius TEXT,
                            load_capacity INTEGER,
                            total_weight INTEGER,
                            cargo_dimensions TEXT,
                            location TEXT,
                            description TEXT,
                            photos TEXT DEFAULT '[]',
                            seller_id INTEGER,
                            is_active BOOLEAN DEFAULT 1,
                            views_count INTEGER DEFAULT 0,
                            published_at TIMESTAMP,
                            published_in_group BOOLEAN DEFAULT 0,
                            published_in_bot BOOLEAN DEFAULT 0,
                            group_message_id INTEGER,
                            bot_message_id INTEGER,
                            vin_code TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (seller_id) REFERENCES users(id)
                        )
                    """)
                    
                    # Копіюємо дані без engine_type
                    await db.execute("""
                        INSERT INTO vehicles_new 
                        SELECT id, brand, model, year, vehicle_type, condition, price,
                               currency, mileage, engine_volume, power_hp, transmission,
                               fuel_type, body_type, wheel_radius, load_capacity, total_weight,
                               cargo_dimensions, location, description, photos, seller_id,
                               is_active, views_count, 
                               published_at,
                               COALESCE(published_in_group, 0) as published_in_group,
                               COALESCE(published_in_bot, 0) as published_in_bot,
                               group_message_id, bot_message_id, vin_code,
                               created_at, updated_at
                        FROM vehicles
                    """)
                    
                    # Видаляємо стару таблицю та перейменовуємо нову
                    await db.execute("DROP TABLE vehicles")
                    await db.execute("ALTER TABLE vehicles_new RENAME TO vehicles")
                    await db.commit()
                    logger.info("✅ Колонка engine_type видалена з таблиці vehicles")
                else:
                    logger.info("ℹ️ Колонка engine_type вже відсутня в таблиці vehicles")
                    
            except Exception as e:
                logger.error(f"❌ Помилка міграції таблиці vehicles: {e}")
            
            # Міграція: додаємо стовпець status якщо його немає
            try:
                await db.execute("ALTER TABLE vehicles ADD COLUMN status TEXT DEFAULT 'available'")
                logger.info("✅ Додано стовпець status до таблиці vehicles")
            except Exception as e:
                # Стовпець вже існує або інша помилка
                logger.info(f"ℹ️ Стовпець status вже існує або помилка: {e}")
            
            # Міграція: додаємо стовпець status_changed_at якщо його немає
            try:
                await db.execute("ALTER TABLE vehicles ADD COLUMN status_changed_at TEXT")
                logger.info("✅ Додано стовпець status_changed_at до таблиці vehicles")
            except Exception as e:
                logger.info(f"ℹ️ Стовпець status_changed_at вже існує або помилка: {e}")
            
            # Міграція: додаємо стовпець sold_at якщо його немає
            try:
                await db.execute("ALTER TABLE vehicles ADD COLUMN sold_at TEXT")
                logger.info("✅ Додано стовпець sold_at до таблиці vehicles")
            except Exception as e:
                logger.info(f"ℹ️ Стовпець sold_at вже існує або помилка: {e}")
            
            # Міграція: додаємо стовпець group_message_id якщо його немає
            try:
                await db.execute("ALTER TABLE vehicles ADD COLUMN group_message_id INTEGER")
                logger.info("✅ Додано стовпець group_message_id до таблиці vehicles")
            except Exception as e:
                logger.info(f"ℹ️ Стовпець group_message_id вже існує або помилка: {e}")
            
            # Міграція: додаємо стовпець bot_message_id якщо його немає
            try:
                await db.execute("ALTER TABLE vehicles ADD COLUMN bot_message_id INTEGER")
                logger.info("✅ Додано стовпець bot_message_id до таблиці vehicles")
            except Exception as e:
                logger.info(f"ℹ️ Стовпець bot_message_id вже існує або помилка: {e}")
            
            await db.commit()

    # Методи для роботи з користувачами
    async def create_user(self, user: UserModel) -> int:
        """Створити нового користувача"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, last_name, 
                                 phone, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user.telegram_id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    user.phone,
                    user.role,
                    user.is_active,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[UserModel]:
        """Отримати користувача за Telegram ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return UserModel(**dict(row)) if row else None

    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Оновити дані користувача"""
        if not updates:
            return False

        updates["updated_at"] = datetime.now()
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [user_id]

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            await db.commit()
            return True

    async def promote_to_admin(self, user_id: int) -> bool:
        """Призначити користувача адміністратором"""
        return await self.update_user(user_id, {"role": "admin"})

    async def demote_from_admin(self, user_id: int) -> bool:
        """Зняти права адміністратора"""
        return await self.update_user(user_id, {"role": "buyer"})

    async def get_admins(self) -> List[UserModel]:
        """Отримати всіх адміністраторів"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM users 
                WHERE role = 'admin' AND is_active = 1
                ORDER BY created_at DESC
            """
            )
            rows = await cursor.fetchall()
            return [UserModel(**dict(row)) for row in rows]

    async def get_buyers(self) -> List[UserModel]:
        """Отримати всіх покупців"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM users 
                WHERE role = 'buyer' AND is_active = 1
                ORDER BY created_at DESC
            """
            )
            rows = await cursor.fetchall()
            return [UserModel(**dict(row)) for row in rows]

    async def get_all_users(self) -> list:
        """Отримати всіх користувачів (для експорту - без валідації)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                # Повертаємо словники без валідації для експорту
                return [dict(row) for row in rows]
    
    async def get_all_vehicles(self) -> list:
        """Отримати всі авто (для експорту - без валідації)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM vehicles ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                # Повертаємо словники без валідації для експорту
                return [dict(row) for row in rows]
    
    async def get_all_requests(self) -> list:
        """Отримати всі заявки"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM manager_requests ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                # Повертаємо як словники, бо RequestModel не існує
                return [dict(row) for row in rows]
    
    async def get_all_broadcasts_raw(self) -> list:
        """Отримати всі розсилки (для експорту - без валідації)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM broadcasts ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                # Повертаємо словники без валідації для експорту
                return [dict(row) for row in rows]

    async def get_users(self, limit: int = 10, offset: int = 0, sort_by: str = "created_at_desc", 
                       status_filter: str = "all") -> List[UserModel]:
        """Отримати користувачів з пагінацією та фільтрацією"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Формуємо WHERE умову для фільтрації
            where_conditions = []
            params = []
            
            if status_filter == "active":
                where_conditions.append("is_active = 1")
            elif status_filter == "blocked":
                where_conditions.append("is_active = 0")
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Формуємо ORDER BY
            order_by = "created_at DESC"
            if sort_by == "created_at_asc":
                order_by = "created_at ASC"
            elif sort_by == "created_at_desc":
                order_by = "created_at DESC"
            elif sort_by == "name_asc":
                order_by = "first_name ASC, last_name ASC"
            elif sort_by == "name_desc":
                order_by = "first_name DESC, last_name DESC"
            elif sort_by == "role_asc":
                order_by = "role ASC"
            elif sort_by == "role_desc":
                order_by = "role DESC"
            
            query = f"""
                SELECT * FROM users 
                {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """
            
            async with db.execute(query, params + [limit, offset]) as cursor:
                rows = await cursor.fetchall()
                return [UserModel(**dict(row)) for row in rows]

    async def get_users_count(self, status_filter: str = "all") -> int:
        """Отримати загальну кількість користувачів з фільтрацією"""
        async with aiosqlite.connect(self.db_path) as db:
            where_conditions = []
            
            if status_filter == "active":
                where_conditions.append("is_active = 1")
            elif status_filter == "blocked":
                where_conditions.append("is_active = 0")
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f"SELECT COUNT(*) as count FROM users {where_clause}"
            
            async with db.execute(query) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        """Отримати користувача за ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return UserModel(**dict(row)) if row else None

    async def block_user(self, user_id: int) -> bool:
        """Заблокувати користувача"""
        return await self.update_user(user_id, {"is_active": False})

    async def unblock_user(self, user_id: int) -> bool:
        """Розблокувати користувача"""
        return await self.update_user(user_id, {"is_active": True})

    async def delete_user(self, user_id: int) -> bool:
        """Видалити користувача"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            await db.commit()
            return True

    async def search_users_by_id(self, user_id: int) -> List[UserModel]:
        """Пошук користувача за ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [UserModel(**dict(row)) for row in rows]

    async def search_users_by_telegram_id(self, telegram_id: int) -> List[UserModel]:
        """Пошук користувача за Telegram ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [UserModel(**dict(row)) for row in rows]

    async def search_users_by_name(self, name: str) -> List[UserModel]:
        """Пошук користувачів за іменем або прізвищем"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            search_term = f"%{name}%"
            async with db.execute(
                """
                SELECT * FROM users 
                WHERE first_name LIKE ? OR last_name LIKE ? OR username LIKE ?
                ORDER BY created_at DESC
                """, (search_term, search_term, search_term)
            ) as cursor:
                rows = await cursor.fetchall()
                return [UserModel(**dict(row)) for row in rows]

    async def search_users_by_phone(self, phone: str) -> List[UserModel]:
        """Пошук користувачів за номером телефону"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            search_term = f"%{phone}%"
            async with db.execute(
                "SELECT * FROM users WHERE phone LIKE ? ORDER BY created_at DESC", (search_term,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [UserModel(**dict(row)) for row in rows]

    async def search_users_by_role(self, role: str) -> List[UserModel]:
        """Пошук користувачів за роллю"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY created_at DESC", (role,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [UserModel(**dict(row)) for row in rows]

    async def search_users_by_username(self, username: str) -> List[UserModel]:
        """Пошук користувачів за username"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            search_term = f"%{username}%"
            async with db.execute(
                "SELECT * FROM users WHERE username LIKE ? ORDER BY created_at DESC", (search_term,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [UserModel(**dict(row)) for row in rows]

    async def get_users_statistics(self) -> Dict[str, Any]:
        """Отримати статистику користувачів"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Загальна кількість користувачів
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                stats['total_users'] = (await cursor.fetchone())[0]
            
            # Активні користувачі
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1") as cursor:
                stats['active_users'] = (await cursor.fetchone())[0]
            
            # Заблоковані користувачі
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 0") as cursor:
                stats['blocked_users'] = (await cursor.fetchone())[0]
            
            # Користувачі по ролях
            async with db.execute("SELECT role, COUNT(*) FROM users GROUP BY role") as cursor:
                role_stats = await cursor.fetchall()
                stats['users_by_role'] = {role: count for role, count in role_stats}
            
            return stats

    # Методи для роботи з авто
    async def create_vehicle(self, vehicle: VehicleModel) -> int:
        """Створити новий автомобіль"""
        async with aiosqlite.connect(self.db_path) as db:
            # Конвертуємо photos в JSON рядок
            photos_json = json.dumps(vehicle.photos) if vehicle.photos else "[]"
            
            # Підготовлюємо дані для вставки
            values = (
                vehicle.brand,                    # 1
                vehicle.model,                    # 2
                vehicle.year,                     # 3
                vehicle.vehicle_type.value,       # 4
                vehicle.condition.value if vehicle.condition else None,  # 5
                vehicle.status.value if vehicle.status else VehicleStatus.AVAILABLE.value,  # 6 status
                vehicle.price,                    # 7
                vehicle.currency,                 # 8
                vehicle.mileage,                  # 9
                vehicle.engine_volume,            # 10
                vehicle.power_hp,                 # 11
                vehicle.wheel_radius,             # 12
                vehicle.body_type,                # 13
                vehicle.transmission,             # 14
                vehicle.load_capacity,            # 15
                vehicle.total_weight,             # 16
                vehicle.cargo_dimensions,         # 17
                vehicle.location,                 # 18
                vehicle.description,              # 19
                vehicle.main_photo,               # 20 main_photo
                vehicle.seller_id,                # 21
                vehicle.created_at.isoformat() if vehicle.created_at else None,   # 22
                vehicle.updated_at.isoformat() if vehicle.updated_at else None,   # 23
                vehicle.fuel_type,                # 24
                vehicle.is_active,                # 25
                vehicle.views_count,              # 26
                vehicle.published_at.isoformat() if vehicle.published_at else None,  # 27 published_at
                vehicle.published_in_group,       # 28 published_in_group
                vehicle.published_in_bot,         # 29 published_in_bot
                vehicle.group_message_id,         # 30 group_message_id
                vehicle.bot_message_id,           # 31 bot_message_id
                photos_json,                      # 32 photos
                vehicle.vin_code,                 # 33 vin_code
                vehicle.status_changed_at.isoformat() if vehicle.status_changed_at else None,  # 34 status_changed_at
                vehicle.sold_at.isoformat() if vehicle.sold_at else None,  # 35 sold_at
            )
            
            logger.info(f"📊 create_vehicle: передаємо {len(values)} значень")
            logger.info(f"📊 create_vehicle: photos_json = {photos_json}")
            
            cursor = await db.execute(
                """
                INSERT INTO vehicles (brand, model, year, vehicle_type, condition, status, price,
                                    currency, mileage, engine_volume, power_hp, wheel_radius,
                                    body_type, transmission, load_capacity, total_weight,
                                    cargo_dimensions, location, description, main_photo,
                                    seller_id, created_at, updated_at, fuel_type, is_active,
                                    views_count, published_at,
                                    published_in_group, published_in_bot, group_message_id,
                                    bot_message_id, photos, vin_code, status_changed_at, sold_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                values,
            )
            await db.commit()
            return cursor.lastrowid

    async def get_vehicles(
        self, limit: int = 20, offset: int = 0, sort_by: str = "created_at_desc"
    ) -> List[VehicleModel]:
        """Отримати список авто з можливістю сортування"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Визначаємо порядок сортування
            order_clause = "ORDER BY created_at DESC"  # За замовчуванням
            if sort_by == "created_at_asc":
                order_clause = "ORDER BY created_at ASC"
            elif sort_by == "created_at_desc":
                order_clause = "ORDER BY created_at DESC"
            elif sort_by == "price_asc":
                order_clause = "ORDER BY price ASC"
            elif sort_by == "price_desc":
                order_clause = "ORDER BY price DESC"
            elif sort_by == "year_asc":
                order_clause = "ORDER BY year ASC"
            elif sort_by == "year_desc":
                order_clause = "ORDER BY year DESC"
            elif sort_by == "brand_asc":
                order_clause = "ORDER BY brand ASC"
            elif sort_by == "brand_desc":
                order_clause = "ORDER BY brand DESC"
            
            async with db.execute(
                f"""
                SELECT * FROM vehicles 
                WHERE is_active = 1
                {order_clause}
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            ) as cursor:
                rows = await cursor.fetchall()
                vehicles = []
                for row in rows:
                    vehicle_data = self._process_vehicle_data(dict(row))
                    vehicles.append(VehicleModel(**vehicle_data))
                return vehicles

    async def get_available_vehicles(
        self, limit: int = 20, offset: int = 0, sort_by: str = "created_at_desc"
    ) -> List[VehicleModel]:
        """Отримати список доступних авто (не проданих) для клієнтів"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Визначаємо порядок сортування
            order_clause = "ORDER BY created_at DESC"  # За замовчуванням
            if sort_by == "created_at_asc":
                order_clause = "ORDER BY created_at ASC"
            elif sort_by == "created_at_desc":
                order_clause = "ORDER BY created_at DESC"
            elif sort_by == "price_asc":
                order_clause = "ORDER BY price ASC"
            elif sort_by == "price_desc":
                order_clause = "ORDER BY price DESC"
            elif sort_by == "year_asc":
                order_clause = "ORDER BY year ASC"
            elif sort_by == "year_desc":
                order_clause = "ORDER BY year DESC"
            elif sort_by == "brand_asc":
                order_clause = "ORDER BY brand ASC"
            elif sort_by == "brand_desc":
                order_clause = "ORDER BY brand DESC"
            
            async with db.execute(
                f"""
                SELECT * FROM vehicles 
                WHERE is_active = 1 AND (status IS NULL OR status != 'sold')
                {order_clause}
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            ) as cursor:
                rows = await cursor.fetchall()
                vehicles = []
                for row in rows:
                    vehicle_data = self._process_vehicle_data(dict(row))
                    vehicles.append(VehicleModel(**vehicle_data))
                return vehicles

    async def get_available_vehicles_by_types(
        self,
        types: List[str],
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at_desc",
    ) -> List[VehicleModel]:
        """Отримати список доступних авто за списком типів (EN значення enum).

        Якщо список порожній, повертає порожній результат.
        """
        if not types:
            return []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            order_clause = "ORDER BY created_at DESC"
            if sort_by == "created_at_asc":
                order_clause = "ORDER BY created_at ASC"
            elif sort_by == "created_at_desc":
                order_clause = "ORDER BY created_at DESC"
            elif sort_by == "price_asc":
                order_clause = "ORDER BY price ASC"
            elif sort_by == "price_desc":
                order_clause = "ORDER BY price DESC"
            elif sort_by == "year_asc":
                order_clause = "ORDER BY year ASC"
            elif sort_by == "year_desc":
                order_clause = "ORDER BY year DESC"
            elif sort_by == "brand_asc":
                order_clause = "ORDER BY brand ASC"
            elif sort_by == "brand_desc":
                order_clause = "ORDER BY brand DESC"

            placeholders = ",".join(["?"] * len(types))
            query = f"""
                SELECT * FROM vehicles
                WHERE is_active = 1
                  AND (status IS NULL OR status != 'sold')
                  AND vehicle_type IN ({placeholders})
                {order_clause}
                LIMIT ? OFFSET ?
            """
            params = list(types) + [limit, offset]
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                vehicles: List[VehicleModel] = []
                for row in rows:
                    vehicle_data = self._process_vehicle_data(dict(row))
                    vehicles.append(VehicleModel(**vehicle_data))
                return vehicles

    async def get_vehicles_count(self) -> int:
        """Отримати загальну кількість активних авто"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) as count FROM vehicles WHERE is_active = 1"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_available_vehicles_count(self) -> int:
        """Отримати кількість доступних авто (не проданих) для клієнтів"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) as count FROM vehicles WHERE is_active = 1 AND (status IS NULL OR status != 'sold')"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def search_vehicles_by_name(self, query: str) -> List[VehicleModel]:
        """Пошук авто за назвою (бренд або модель)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            search_term = f"%{query.lower()}%"
            async with db.execute(
                """
                SELECT * FROM vehicles 
                WHERE is_active = 1 
                AND (status IS NULL OR status != 'sold')
                AND (LOWER(brand) LIKE ? OR LOWER(model) LIKE ?)
                ORDER BY created_at DESC
            """,
                (search_term, search_term),
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    async def get_vehicle_by_id(self, vehicle_id: int) -> Optional[VehicleModel]:
        """Отримати авто за ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return VehicleModel(**self._process_vehicle_data(dict(row))) if row else None

    async def get_vehicle_by_id_from_message_id(self, message_id: int) -> Optional[VehicleModel]:
        """Отримати авто за group_message_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM vehicles WHERE group_message_id = ?", (message_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return VehicleModel(**self._process_vehicle_data(dict(row))) if row else None

    async def search_vehicles(self, filters: Dict[str, Any]) -> List[VehicleModel]:
        """Пошук авто за фільтрами"""
        where_conditions = []
        params = []

        for key, value in filters.items():
            if value is not None:
                if key in ["min_price"]:
                    where_conditions.append("price >= ?")
                    params.append(value)
                elif key in ["max_price"]:
                    where_conditions.append("price <= ?")
                    params.append(value)
                elif key in ["min_year"]:
                    where_conditions.append("year >= ?")
                    params.append(value)
                elif key in ["max_year"]:
                    where_conditions.append("year <= ?")
                    params.append(value)
                elif key in ["max_mileage"]:
                    where_conditions.append("mileage <= ?")
                    params.append(value)
                elif key in ["min_load_capacity"]:
                    where_conditions.append("load_capacity >= ?")
                    params.append(value)
                elif key in ["max_load_capacity"]:
                    where_conditions.append("load_capacity <= ?")
                    params.append(value)
                elif key in ["brand"]:
                    where_conditions.append("LOWER(brand) LIKE LOWER(?)")
                    params.append(f"%{value}%")
                elif key in ["location"]:
                    where_conditions.append("LOWER(location) LIKE LOWER(?)")
                    params.append(f"%{value}%")
                elif key in ["engine_type"]:
                    where_conditions.append("LOWER(engine_type) LIKE LOWER(?)")
                    params.append(f"%{value}%")
                elif key in ["fuel_type"]:
                    where_conditions.append("LOWER(fuel_type) LIKE LOWER(?)")
                    params.append(f"%{value}%")
                elif key in ["condition"]:
                    where_conditions.append("condition = ?")
                    params.append(value)
                elif key in ["vehicle_type"]:
                    where_conditions.append("vehicle_type = ?")
                    params.append(value)
                elif key == "sort_by":
                    continue  # Обробляємо сортування окремо
                else:
                    where_conditions.append(f"{key} = ?")
                    params.append(value)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Визначаємо сортування
        sort_by = filters.get("sort_by", "created_at_desc")
        order_clause = self._get_sort_clause(sort_by)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"""
                SELECT * FROM vehicles 
                WHERE {where_clause}
                ORDER BY {order_clause}
            """,
                params,
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    def _get_sort_clause(self, sort_by: str) -> str:
        """Отримати SQL для сортування"""
        sort_mapping = {
            "price_asc": "price ASC",
            "price_desc": "price DESC",
            "year_asc": "year ASC",
            "year_desc": "year DESC",
            "mileage_asc": "mileage ASC",
            "mileage_desc": "mileage DESC",
            "date_desc": "created_at DESC",
            "date_asc": "created_at ASC",
        }
        return sort_mapping.get(sort_by, "created_at DESC")

    # ===== Групові гілки та розсилки =====

    async def upsert_group_topic(self, thread_id: int, name: str) -> int:
        """Додати або оновити гілку групи"""
        async with aiosqlite.connect(self.db_path) as db:
            # Спробуємо оновити, якщо існує
            await db.execute(
                "UPDATE group_topics SET name = ? WHERE thread_id = ?",
                (name, thread_id),
            )
            await db.execute(
                "INSERT INTO group_topics (thread_id, name) SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM group_topics WHERE thread_id = ?)",
                (thread_id, name, thread_id),
            )
            await db.commit()
            # Повернемо id
            async with db.execute("SELECT id FROM group_topics WHERE thread_id = ?", (thread_id,)) as c:
                row = await c.fetchone()
                return row[0]

    async def get_group_topics(self) -> List[GroupTopicModel]:
        """Отримати всі збережені гілки групи"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM group_topics ORDER BY name ASC") as c:
                rows = await c.fetchall()
                return [GroupTopicModel(**dict(r)) for r in rows]

    async def delete_group_topic(self, thread_id: int) -> None:
        """Видалити гілку групи за thread_id"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM group_topics WHERE thread_id = ?", (thread_id,))
            await db.commit()

    async def update_group_topic_thread_id(self, old_thread_id: int, new_thread_id: int) -> None:
        """Оновити thread_id гілки"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE group_topics SET thread_id = ? WHERE thread_id = ?",
                (new_thread_id, old_thread_id),
            )
            await db.commit()

    async def create_broadcast(self, data: Dict[str, Any]) -> int:
        """Зберегти чернетку/історію розсилки"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO broadcasts (text, button_text, button_url, media_type, media_file_id, media_group_id, status, schedule_period, scheduled_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    data.get("text"),
                    data.get("button_text"),
                    data.get("button_url"),
                    data.get("media_type"),
                    data.get("media_file_id"),
                    data.get("media_group_id"),
                    data.get("status", "draft"),
                    data.get("schedule_period", "none"),
                    data.get("scheduled_at"),
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def list_broadcasts(
        self, 
        limit: int = 20, 
        offset: int = 0, 
        sort_by: str = "created_at_desc",
        status_filter: str = "all"
    ) -> List[BroadcastModel]:
        """Отримати список розсилок з пагінацією, сортуванням та фільтрацією"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Визначаємо сортування
            if sort_by == "created_at_desc":
                order_clause = "ORDER BY created_at DESC"
            elif sort_by == "created_at_asc":
                order_clause = "ORDER BY created_at ASC"
            else:
                order_clause = "ORDER BY created_at DESC"
            
            # Визначаємо фільтр статусу
            if status_filter == "sent":
                where_clause = "WHERE status = 'sent'"
            elif status_filter == "draft":
                where_clause = "WHERE status = 'draft'"
            else:
                where_clause = ""
            
            query = f"SELECT * FROM broadcasts {where_clause} {order_clause} LIMIT ? OFFSET ?"
            async with db.execute(query, (limit, offset)) as c:
                rows = await c.fetchall()
                broadcasts = []
                for row in rows:
                    broadcast_data = dict(row)
                    # Обробка дат
                    if broadcast_data.get('created_at'):
                        if isinstance(broadcast_data['created_at'], str):
                            broadcast_data['created_at'] = datetime.fromisoformat(broadcast_data['created_at'])
                    if broadcast_data.get('scheduled_at'):
                        if isinstance(broadcast_data['scheduled_at'], str):
                            broadcast_data['scheduled_at'] = datetime.fromisoformat(broadcast_data['scheduled_at'])
                    broadcasts.append(BroadcastModel(**broadcast_data))
                return broadcasts
    
    async def get_broadcasts_count(self, status_filter: str = "all") -> int:
        """Отримати загальну кількість розсилок з фільтром"""
        async with aiosqlite.connect(self.db_path) as db:
            if status_filter == "sent":
                query = "SELECT COUNT(*) FROM broadcasts WHERE status = 'sent'"
            elif status_filter == "draft":
                query = "SELECT COUNT(*) FROM broadcasts WHERE status = 'draft'"
            else:
                query = "SELECT COUNT(*) FROM broadcasts"
            
            async with db.execute(query) as c:
                row = await c.fetchone()
                return row[0] if row else 0
    
    async def get_broadcasts_statistics(self) -> dict:
        """Отримати статистику розсилок"""
        async with aiosqlite.connect(self.db_path) as db:
            total = await self.get_broadcasts_count("all")
            sent = await self.get_broadcasts_count("sent")
            draft = await self.get_broadcasts_count("draft")
            
            return {
                'total_broadcasts': total,
                'sent_broadcasts': sent,
                'draft_broadcasts': draft,
            }
    
    async def get_broadcast_by_id(self, broadcast_id: int) -> Optional[BroadcastModel]:
        """Отримати розсилку за ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM broadcasts WHERE id = ?", (broadcast_id,)) as c:
                row = await c.fetchone()
                if not row:
                    return None
                
                broadcast_data = dict(row)
                # Обробка дат
                if broadcast_data.get('created_at'):
                    if isinstance(broadcast_data['created_at'], str):
                        broadcast_data['created_at'] = datetime.fromisoformat(broadcast_data['created_at'])
                if broadcast_data.get('scheduled_at'):
                    if isinstance(broadcast_data['scheduled_at'], str):
                        broadcast_data['scheduled_at'] = datetime.fromisoformat(broadcast_data['scheduled_at'])
                
                return BroadcastModel(**broadcast_data)

    async def delete_broadcast(self, broadcast_id: int) -> bool:
        """Видалити розсилку з БД"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM broadcasts WHERE id = ?", (broadcast_id,))
                await db.commit()
                logger.info(f"✅ Розсилку {broadcast_id} видалено з БД")
                return True
        except Exception as e:
            logger.error(f"❌ Помилка видалення розсилки {broadcast_id}: {e}")
            return False

    # ===== Збережені авто =====

    async def save_vehicle(
        self, user_id: int, vehicle_id: int, notes: str = None
    ) -> int:
        """Зберегти авто для покупця"""
        from .models import SavedVehicleModel

        # Перевіряємо чи вже збережено
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT id FROM saved_vehicles 
                WHERE user_id = ? AND vehicle_id = ?
            """,
                (user_id, vehicle_id),
            ) as cursor:
                existing = await cursor.fetchone()
                if existing:
                    return existing[0]  # Вже збережено

        # Зберігаємо нове
        saved_vehicle = SavedVehicleModel(
            user_id=user_id, vehicle_id=vehicle_id, notes=notes
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO saved_vehicles 
                (user_id, vehicle_id, notes, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    saved_vehicle.user_id,
                    saved_vehicle.vehicle_id,
                    saved_vehicle.notes,
                    saved_vehicle.created_at.isoformat(),
                ),
            )
            await db.commit()

            # Отримуємо ID нового запису
            async with db.execute("SELECT last_insert_rowid()") as cursor:
                result = await cursor.fetchone()
                return result[0]

    async def remove_saved_vehicle(self, user_id: int, vehicle_id: int) -> bool:
        """Видалити авто з збережених"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM saved_vehicles 
                WHERE user_id = ? AND vehicle_id = ?
            """,
                (user_id, vehicle_id),
            )
            await db.commit()
            return True

    async def get_saved_vehicles(self, user_id: int) -> list:
        """Отримати всі збережені авто покупця"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT v.*, sv.notes, sv.created_at as saved_at
                FROM saved_vehicles sv
                JOIN vehicles v ON sv.vehicle_id = v.id
                WHERE sv.user_id = ?
                ORDER BY sv.created_at DESC
            """,
                (user_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def is_vehicle_saved(self, user_id: int, vehicle_id: int) -> bool:
        """Перевірити чи збережено авто покупцем"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT 1 FROM saved_vehicles 
                WHERE user_id = ? AND vehicle_id = ?
            """,
                (user_id, vehicle_id),
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None

    async def update_saved_vehicle_notes(
        self, user_id: int, vehicle_id: int, notes: str = None
    ) -> bool:
        """Оновити нотатки до збереженого авто"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE saved_vehicles 
                SET notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND vehicle_id = ?
            """,
                (notes, user_id, vehicle_id),
            )
            await db.commit()
            return True

    async def update_saved_vehicle_category(
        self, user_id: int, vehicle_id: int, category: str
    ) -> bool:
        """Оновити категорію збереженого авто"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE saved_vehicles 
                SET category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND vehicle_id = ?
            """,
                (category, user_id, vehicle_id),
            )
            await db.commit()
            return True

    async def get_saved_vehicles_by_category(
        self, user_id: int, category: str = None
    ) -> list:
        """Отримати збережені авто за категорією"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if category:
                query = """
                    SELECT v.*, sv.notes, sv.category, sv.created_at as saved_at
                    FROM saved_vehicles sv
                    JOIN vehicles v ON sv.vehicle_id = v.id
                    WHERE sv.user_id = ? AND sv.category = ?
                    ORDER BY sv.created_at DESC
                """
                params = (user_id, category)
            else:
                query = """
                    SELECT v.*, sv.notes, sv.category, sv.created_at as saved_at
                    FROM saved_vehicles sv
                    JOIN vehicles v ON sv.vehicle_id = v.id
                    WHERE sv.user_id = ?
                    ORDER BY sv.created_at DESC
                """
                params = (user_id,)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ===== Заявки менеджеру =====

    async def create_manager_request(
        self, user_id: int, request_type: str, details: str, vehicle_id: int | None = None
    ) -> int:
        """Створити заявку менеджеру"""
        from .models import ManagerRequestModel

        request = ManagerRequestModel(
            user_id=user_id, request_type=request_type, details=details
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO manager_requests 
                (user_id, vehicle_id, request_type, details, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request.user_id,
                    vehicle_id,
                    request.request_type,
                    request.details,
                    request.status,
                    request.created_at.isoformat(),
                    request.updated_at.isoformat(),
                ),
            )
            await db.commit()

            # Отримуємо ID нового запису
            async with db.execute("SELECT last_insert_rowid()") as cursor:
                result = await cursor.fetchone()
                return result[0]

    async def get_manager_requests(self, user_id: int = None, status_filter: str = "all", sort: str = "newest", limit: int | None = None, offset: int | None = None) -> list:
        """Отримати заявки менеджеру з фільтрами та пагінацією"""
        query = """
            SELECT mr.*, u.first_name, u.last_name, u.phone,
                   v.id as vehicle_id_ref, v.brand as vehicle_brand, v.model as vehicle_model, v.price as vehicle_price
            FROM manager_requests mr
            JOIN users u ON mr.user_id = u.id
            LEFT JOIN vehicles v ON v.id = mr.vehicle_id
        """
        params = []

        where_clauses = []
        if user_id:
            where_clauses.append("mr.user_id = ?")
            params.append(user_id)
        if status_filter in {"new", "done", "cancelled"}:
            where_clauses.append("mr.status = ?")
            params.append(status_filter)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        # Сортування: за датою або за ім'ям
        if sort in ("newest", "date_desc"):
            order_sql = "mr.created_at DESC"
        elif sort in ("oldest", "date_asc"):
            order_sql = "mr.created_at ASC"
        elif sort == "name_asc":
            order_sql = "LOWER(TRIM(u.first_name || ' ' || IFNULL(u.last_name,''))) ASC"
        elif sort == "name_desc":
            order_sql = "LOWER(TRIM(u.first_name || ' ' || IFNULL(u.last_name,''))) DESC"
        else:
            order_sql = "mr.created_at DESC"

        query += f" ORDER BY {order_sql}"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_manager_requests_count(self, status_filter: str = "all") -> int:
        """Повернути кількість заявок з урахуванням фільтра"""
        query = "SELECT COUNT(*) FROM manager_requests"
        params = []
        if status_filter in {"new", "done", "cancelled"}:
            query += " WHERE status = ?"
            params.append(status_filter)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return int(row[0])

    async def get_manager_requests_stats(self) -> dict:
        """Повернути статистику заявок: total/new/done/cancelled"""
        async with aiosqlite.connect(self.db_path) as db:
            # Загальна
            async with db.execute("SELECT COUNT(*) FROM manager_requests") as c1:
                total = int((await c1.fetchone())[0])
            # Нові
            async with db.execute("SELECT COUNT(*) FROM manager_requests WHERE status = 'new'") as c2:
                new_cnt = int((await c2.fetchone())[0])
            # Опрацьовані
            async with db.execute("SELECT COUNT(*) FROM manager_requests WHERE status = 'done'") as c3:
                done_cnt = int((await c3.fetchone())[0])
            # Скасовані
            async with db.execute("SELECT COUNT(*) FROM manager_requests WHERE status = 'cancelled'") as c4:
                cancelled_cnt = int((await c4.fetchone())[0])
        return {"total": total, "new": new_cnt, "done": done_cnt, "cancelled": cancelled_cnt}

    async def update_manager_request_status(self, request_id: int, status: str, admin_id: int = None) -> None:
        """Оновити статус заявки з логуванням адміністратора"""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            if admin_id:
                # Якщо передано admin_id, зберігаємо його разом з часом обробки
                await db.execute(
                    """UPDATE manager_requests 
                       SET status = ?, updated_at = ?, processed_by_admin_id = ?, processed_at = ? 
                       WHERE id = ?""",
                    (status, now, admin_id, now, request_id),
                )
            else:
                # Стара логіка для зворотної сумісності
                await db.execute(
                    "UPDATE manager_requests SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, request_id),
                )
            await db.commit()

    # ===== Історія пошуків =====

    async def save_search_history(
        self, user_id: int, search_params: dict, results_count: int = 0
    ) -> int:
        """Зберегти пошук в історію"""
        # Генеруємо назву пошуку на основі параметрів
        search_name = self._generate_search_name(search_params)

        search_history = SearchHistoryModel(
            user_id=user_id,
            search_name=search_name,
            vehicle_type=search_params.get("vehicle_type"),
            brand=search_params.get("brand"),
            min_year=search_params.get("min_year"),
            max_year=search_params.get("max_year"),
            min_price=search_params.get("min_price"),
            max_price=search_params.get("max_price"),
            max_mileage=search_params.get("max_mileage"),
            location=search_params.get("location"),
            engine_type=search_params.get("engine_type"),
            fuel_type=search_params.get("fuel_type"),
            load_capacity=search_params.get("load_capacity"),
            condition=search_params.get("condition"),
            results_count=results_count,
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO search_history 
                (user_id, search_name, vehicle_type, brand, min_year, max_year, 
                 min_price, max_price, max_mileage, location, engine_type, 
                 fuel_type, load_capacity, condition, results_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    search_history.user_id,
                    search_history.search_name,
                    search_history.vehicle_type,
                    search_history.brand,
                    search_history.min_year,
                    search_history.max_year,
                    search_history.min_price,
                    search_history.max_price,
                    search_history.max_mileage,
                    search_history.location,
                    search_history.engine_type,
                    search_history.fuel_type,
                    search_history.load_capacity,
                    search_history.condition,
                    search_history.results_count,
                    search_history.created_at.isoformat(),
                ),
            )
            await db.commit()

            # Отримуємо ID нового запису
            async with db.execute("SELECT last_insert_rowid()") as cursor:
                result = await cursor.fetchone()
                return result[0]

    def _generate_search_name(self, search_params: dict) -> str:
        """Генерує назву пошуку на основі параметрів"""
        parts = []

        if search_params.get("vehicle_type"):
            parts.append(f"Тип: {search_params['vehicle_type']}")

        if search_params.get("brand"):
            parts.append(f"Марка: {search_params['brand']}")

        if search_params.get("min_year") or search_params.get("max_year"):
            year_range = []
            if search_params.get("min_year"):
                year_range.append(f"від {search_params['min_year']}")
            if search_params.get("max_year"):
                year_range.append(f"до {search_params['max_year']}")
            parts.append(f"Рік: {' '.join(year_range)}")

        if search_params.get("min_price") or search_params.get("max_price"):
            price_range = []
            if search_params.get("min_price"):
                price_range.append(f"від ${search_params['min_price']:,.0f}")
            if search_params.get("max_price"):
                price_range.append(f"до ${search_params['max_price']:,.0f}")
            parts.append(f"Ціна: {' '.join(price_range)}")

        if search_params.get("location"):
            parts.append(f"Місце: {search_params['location']}")

        if not parts:
            return "Загальний пошук"

        return " | ".join(parts)

    async def get_search_history(self, user_id: int, limit: int = 10) -> List[dict]:
        """Отримати історію пошуків користувача"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM search_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """,
                (user_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def delete_search_history(self, user_id: int, search_id: int = None) -> bool:
        """Видалити пошук з історії"""
        async with aiosqlite.connect(self.db_path) as db:
            if search_id:
                await db.execute(
                    """
                    DELETE FROM search_history 
                    WHERE user_id = ? AND id = ?
                """,
                    (user_id, search_id),
                )
            else:
                await db.execute(
                    """
                    DELETE FROM search_history 
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
            await db.commit()
            return True

    # ===== Підписки =====

    async def create_subscription(
        self, user_id: int, subscription_name: str, search_params: dict
    ) -> int:
        """Створити підписку на сповіщення"""
        subscription = SubscriptionModel(
            user_id=user_id,
            subscription_name=subscription_name,
            vehicle_type=search_params.get("vehicle_type"),
            brand=search_params.get("brand"),
            min_year=search_params.get("min_year"),
            max_year=search_params.get("max_year"),
            min_price=search_params.get("min_price"),
            max_price=search_params.get("max_price"),
            max_mileage=search_params.get("max_mileage"),
            location=search_params.get("location"),
            engine_type=search_params.get("engine_type"),
            fuel_type=search_params.get("fuel_type"),
            load_capacity=search_params.get("load_capacity"),
            condition=search_params.get("condition"),
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO subscriptions 
                (user_id, subscription_name, vehicle_type, brand, min_year, max_year, 
                 min_price, max_price, max_mileage, location, engine_type, 
                 fuel_type, load_capacity, condition, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    subscription.user_id,
                    subscription.subscription_name,
                    subscription.vehicle_type,
                    subscription.brand,
                    subscription.min_year,
                    subscription.max_year,
                    subscription.min_price,
                    subscription.max_price,
                    subscription.max_mileage,
                    subscription.location,
                    subscription.engine_type,
                    subscription.fuel_type,
                    subscription.load_capacity,
                    subscription.condition,
                    subscription.is_active,
                    subscription.created_at.isoformat(),
                    subscription.created_at.isoformat(),
                ),
            )
            await db.commit()

            # Отримуємо ID нового запису
            async with db.execute("SELECT last_insert_rowid()") as cursor:
                result = await cursor.fetchone()
                return result[0]

    async def get_user_subscriptions(self, user_id: int) -> List[dict]:
        """Отримати підписки користувача"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM subscriptions 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """,
                (user_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_subscription_status(
        self, subscription_id: int, is_active: bool
    ) -> bool:
        """Оновити статус підписки"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE subscriptions 
                SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (is_active, subscription_id),
            )
            await db.commit()
            return True

    async def delete_subscription(self, user_id: int, subscription_id: int) -> bool:
        """Видалити підписку"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM subscriptions 
                WHERE user_id = ? AND id = ?
            """,
                (user_id, subscription_id),
            )
            await db.commit()
            return True

    async def get_active_subscriptions(self) -> List[dict]:
        """Отримати всі активні підписки (для перевірки нових авто)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM subscriptions 
                WHERE is_active = 1
                ORDER BY created_at DESC
            """
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def find_vehicles_for_subscription(self, subscription: dict) -> List[VehicleModel]:
        """Знайти авто що відповідають критеріям підписки"""
        query = "SELECT * FROM vehicles WHERE status = 'available'"
        params = []
        
        if subscription.get('vehicle_type'):
            query += " AND vehicle_type = ?"
            params.append(subscription['vehicle_type'])
        
        if subscription.get('brand'):
            query += " AND brand = ?"
            params.append(subscription['brand'])
        
        if subscription.get('min_year'):
            query += " AND year >= ?"
            params.append(subscription['min_year'])
        
        if subscription.get('max_year'):
            query += " AND year <= ?"
            params.append(subscription['max_year'])
        
        if subscription.get('min_price'):
            query += " AND price >= ?"
            params.append(subscription['min_price'])
        
        if subscription.get('max_price'):
            query += " AND price <= ?"
            params.append(subscription['max_price'])
        
        if subscription.get('max_mileage'):
            query += " AND mileage <= ?"
            params.append(subscription['max_mileage'])
        
        if subscription.get('condition'):
            query += " AND condition = ?"
            params.append(subscription['condition'])
        
        # Додаємо фільтр тільки для нових авто (створених після останнього сповіщення)
        if subscription.get('last_notification'):
            query += " AND created_at > ?"
            params.append(subscription['last_notification'])
        
        query += " ORDER BY created_at DESC"
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                vehicles = []
                for row in rows:
                    vehicle_data = dict(row)
                    vehicle_data = self._process_vehicle_data(vehicle_data)
                    vehicles.append(VehicleModel(**vehicle_data))
                return vehicles
    
    async def update_subscription_last_notification(self, subscription_id: int) -> bool:
        """Оновити час останнього сповіщення для підписки"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE subscriptions 
                SET last_notification = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (subscription_id,),
            )
            await db.commit()
            return True

    # ===== МЕТОДИ ДЛЯ РОБОТИ З ФОТО =====

    async def add_photo(
        self, vehicle_id: int, file_id: str, file_path: str, is_main: bool = False
    ) -> int:
        """Додати фото до авто"""
        async with aiosqlite.connect(self.db_path) as db:
            # Якщо це головне фото, знімаємо статус головного з інших фото
            if is_main:
                await db.execute(
                    """
                    UPDATE photos SET is_main = 0 
                    WHERE vehicle_id = ?
                """,
                    (vehicle_id,),
                )

            # Додаємо нове фото
            cursor = await db.execute(
                """
                INSERT INTO photos (vehicle_id, file_id, file_path, is_main)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (vehicle_id, file_id, file_path, is_main),
            )
            await db.commit()
            return cursor.lastrowid

    async def update_vehicle(self, vehicle_id: int, update_data: dict) -> bool:
        """Оновити авто"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Підготовлюємо SQL запит для оновлення
                set_clauses = []
                values = []
                
                for field, value in update_data.items():
                    if field in ["vehicle_type", "condition"] and hasattr(value, 'value'):
                        value = value.value
                    elif field == "photos" and isinstance(value, list):
                        value = json.dumps(value)
                    elif field in ["created_at", "updated_at"] and hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
                
                if not set_clauses:
                    return False
                
                # Додаємо updated_at
                set_clauses.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                
                # Додаємо vehicle_id
                values.append(vehicle_id)
                
                sql = f"UPDATE vehicles SET {', '.join(set_clauses)} WHERE id = ?"
                
                await db.execute(sql, values)
                await db.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Помилка оновлення авто: {e}")
            return False

    def _parse_media_id(self, raw_id: str) -> tuple[str, str]:
        """Розпізнати тип медіа зі збереженого рядка.

        Підтримка форматів:
        - "video:<file_id>" → ("video", <file_id>)
        - інше → ("photo", raw_id)
        """
        try:
            if isinstance(raw_id, str) and raw_id.startswith("video:"):
                return "video", raw_id.split(":", 1)[1]
        except Exception:
            pass
        return "photo", raw_id

    async def get_vehicle_photos(self, vehicle_id: int) -> List[dict]:
        """Отримати всі фото/відео авто (з урахуванням типу)"""
        # Отримуємо авто з БД
        vehicle = await self.get_vehicle_by_id(vehicle_id)
        if not vehicle or not vehicle.photos:
            return []
        
        # Повертаємо всі медіа як список словників; головне визначається через main_photo
        photos = []
        for i, photo_id in enumerate(vehicle.photos):
            media_type, file_id = self._parse_media_id(photo_id)
            main_media_type, main_file_id = self._parse_media_id(vehicle.main_photo) if vehicle.main_photo else (None, None)
            photos.append({
                "id": i + 1,
                "vehicle_id": vehicle_id,
                "file_id": file_id,
                "type": media_type,
                "file_path": "",
                "is_main": (file_id == main_file_id),
                "created_at": vehicle.created_at
            })
        
        return photos

    async def get_main_photo(self, vehicle_id: int) -> Optional[dict]:
        """Отримати головне медіа авто (фото або відео)"""
        # Спочатку отримуємо авто з БД
        vehicle = await self.get_vehicle_by_id(vehicle_id)
        if not vehicle or not vehicle.photos or len(vehicle.photos) == 0:
            return None
        
        # Якщо задано main_photo — повертаємо його з визначеним типом
        if vehicle.main_photo:
            media_type, file_id = self._parse_media_id(vehicle.main_photo)
            return {
                "file_id": file_id,
                "type": media_type,
                "vehicle_id": vehicle_id,
                "is_main": True
            }
        return None

    async def delete_vehicle(self, vehicle_id: int) -> bool:
        """Видалити авто"""
        async with aiosqlite.connect(self.db_path) as db:
            # Видаляємо пов'язані записи
            await db.execute("DELETE FROM saved_vehicles WHERE vehicle_id = ?", (vehicle_id,))
            
            # Видаляємо авто
            await db.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
            await db.commit()
            return True

    async def get_vehicles_by_status(self, status: str, page: int = 1, per_page: int = 10, sort_by: str = "created_at_desc") -> List[VehicleModel]:
        """Отримати авто за статусом з пагінацією та сортуванням"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Визначаємо порядок сортування
            order_clause = "ORDER BY created_at DESC"
            if sort_by == "created_at_asc":
                order_clause = "ORDER BY created_at ASC"
            elif sort_by == "price_desc":
                order_clause = "ORDER BY price DESC"
            elif sort_by == "price_asc":
                order_clause = "ORDER BY price ASC"
            
            # Обчислюємо offset для пагінації
            offset = (page - 1) * per_page
            
            async with db.execute(
                f"SELECT * FROM vehicles WHERE status = ? {order_clause} LIMIT ? OFFSET ?",
                (status, per_page, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    async def get_vehicles_count_by_status(self, status: str) -> int:
        """Отримати кількість авто за статусом"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM vehicles WHERE status = ?",
                (status,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def delete_all_vehicles(self) -> int:
        """Видалити всі авто"""
        async with aiosqlite.connect(self.db_path) as db:
            # Видаляємо всі пов'язані записи
            await db.execute("DELETE FROM saved_vehicles")
            await db.execute("DELETE FROM photos")
            
            # Видаляємо всі авто
            cursor = await db.execute("DELETE FROM vehicles")
            await db.commit()
            return cursor.rowcount

    # Методи швидкого пошуку
    async def search_vehicles_by_vin(self, vin_code: str) -> List[VehicleModel]:
        """Пошук авто по VIN коду"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM vehicles WHERE vin_code LIKE ?",
                (f"%{vin_code}%",)
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    async def search_vehicles_by_brand(self, brand: str) -> List[VehicleModel]:
        """Пошук авто по марці"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM vehicles WHERE brand LIKE ?",
                (f"%{brand}%",)
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    async def search_vehicles_by_model(self, model: str) -> List[VehicleModel]:
        """Пошук авто по моделі"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM vehicles WHERE model LIKE ?",
                (f"%{model}%",)
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    async def search_vehicles_by_brand_model(self, query: str) -> List[VehicleModel]:
        """Пошук авто по марці АБО моделі (об'єднаний пошук)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            like = f"%{query}%"
            async with db.execute(
                "SELECT * FROM vehicles WHERE brand LIKE ? OR model LIKE ?",
                (like, like)
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    async def search_vehicles_by_brand_and_model(self, brand: str, model: str) -> List[VehicleModel]:
        """Пошук авто по марці ТА моделі (послідовний пошук)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            brand_like = f"%{brand}%"
            model_like = f"%{model}%"
            async with db.execute(
                """
                SELECT * FROM vehicles 
                WHERE is_active = 1 
                AND (status IS NULL OR status != 'sold')
                AND brand LIKE ? AND model LIKE ?
                ORDER BY created_at DESC
                """,
                (brand_like, model_like)
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    async def search_vehicles_by_years(self, year_from: int, year_to: int) -> List[VehicleModel]:
        """Пошук авто по діапазону років"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM vehicles 
                WHERE is_active = 1 
                AND (status IS NULL OR status != 'sold')
                AND year >= ? AND year <= ? 
                ORDER BY year DESC
                """,
                (year_from, year_to)
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]

    async def search_vehicles_by_price_range(self, price_from: float, price_to: float) -> List[VehicleModel]:
        """Пошук авто по діапазону цін"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM vehicles 
                WHERE is_active = 1 
                AND (status IS NULL OR status != 'sold')
                AND price >= ? AND price <= ? 
                ORDER BY price ASC
                """,
                (price_from, price_to)
            ) as cursor:
                rows = await cursor.fetchall()
                return [VehicleModel(**self._process_vehicle_data(dict(row))) for row in rows]


# Глобальний екземпляр менеджера бази даних
db_manager = DatabaseManager()
