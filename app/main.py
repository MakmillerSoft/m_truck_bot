"""
Головний файл запуску бота
"""

import asyncio
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher

from .config.settings import settings
from .config.storage import create_storage


# Налаштування логування
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_bot() -> Bot:
    """Створити екземпляр бота"""
    return Bot(token=settings.bot_token)


async def create_dispatcher() -> Dispatcher:
    """Створити диспетчер з обробниками"""
    storage = create_storage()
    dp = Dispatcher(storage=storage)

    # Підключення middleware
    from .middleware.state_guard import StateGuardMiddleware
    from .middleware.active_user_guard import ActiveUserGuardMiddleware

    dp.message.middleware(StateGuardMiddleware())
    dp.message.middleware(ActiveUserGuardMiddleware())
    dp.callback_query.middleware(ActiveUserGuardMiddleware())

    # Підключення роутерів
    from .handlers.global_handlers import router as global_router
    from .modules.admin import router as admin_router
    # Новий клієнтський модуль
    from .modules.client import router as client_router
    
    # Старі клієнтські модулі (відключено)
    # from .modules.auth.handlers import router as auth_router
    # from .modules.profile.handlers import router as profile_router
    # from .modules.search.handlers import router as search_router
    # from .modules.info.handlers import router as info_router
    # from .modules.messages.handlers import router as messages_router

    # Порядок роутерів - адмін панель має вищий пріоритет
    dp.include_router(global_router)
    # Новий клієнтський модуль ПЕРЕД адмін панеллю, щоб клієнтські хендлери мали нижчий пріоритет за адмінські
    dp.include_router(client_router)
    dp.include_router(admin_router)  # Адмін панель ПЕРЕД пошуком
    # dp.include_router(auth_router)
    # dp.include_router(profile_router)
    # dp.include_router(search_router)
    # dp.include_router(info_router)
    # dp.include_router(messages_router)

    return dp


async def main():
    """Головна функція запуску бота"""
    # Завантаження змінних середовища
    load_dotenv()

    logger.info("Запуск M-Truck Bot...")

    try:
        # Ініціалізація бази даних
        from .modules.database.manager import db_manager

        await db_manager.init_database()
        logger.info("База даних ініціалізована")

        # Інформація про FSM storage (без створення нового)
        storage_type = getattr(settings, "fsm_storage_type", "memory")
        logger.info(f"FSM Storage type configured: {storage_type}")

        # Створення бота та диспетчера
        bot = await create_bot()
        dp = await create_dispatcher()

        # Ініціалізація GroupPublisher
        from .modules.group.publisher import init_group_publisher

        group_publisher = init_group_publisher(bot)
        logger.info(
            f"GroupPublisher ініціалізовано (увімкнено: {group_publisher.is_enabled()})"
        )

        # Перевірка підключення з таймаутом
        try:
            bot_info = await asyncio.wait_for(bot.get_me(), timeout=10.0)
            logger.info(f"Бот {bot_info.username} успішно запущений!")
        except asyncio.TimeoutError:
            logger.error("Таймаут при підключенні до Telegram API (10 секунд)")
            logger.error(
                "Можливі причини: проблеми з мережею, блокування Telegram, неправильний токен"
            )
            raise
        except Exception as e:
            logger.error(f"Помилка при отриманні інформації про бота: {e}")
            raise

        # Запуск polling
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Помилка при запуску бота: {e}")
    finally:
        logger.info("Бот зупинений")


if __name__ == "__main__":
    asyncio.run(main())
