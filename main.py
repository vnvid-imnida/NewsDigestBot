"""News Digest Bot - Main entry point."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from database.connection import close_db, init_db
from handlers import ErrorHandlingMiddleware
from handlers import digest as digest_handler
from handlers import library as library_handler
from handlers import schedule as schedule_handler
from handlers import settings as settings_handler
from handlers import start
from handlers import stats as stats_handler
from services.news_api import news_api_service
from services.scheduler import start_scheduler, stop_scheduler

# Configure logging - use stdout for Docker compatibility
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=settings.bot_token)
dp = Dispatcher(storage=MemoryStorage())


async def on_startup() -> None:
    """Initialize services on bot startup."""
    logger.info("Starting News Digest Bot...")
    await init_db()
    logger.info("Database connection initialized")
    await start_scheduler(bot)
    logger.info("Scheduler started")


async def on_shutdown() -> None:
    """Cleanup on bot shutdown."""
    logger.info("Shutting down News Digest Bot...")
    await stop_scheduler()
    logger.info("Scheduler stopped")
    await news_api_service.close()
    await close_db()
    logger.info("All connections closed")


async def main() -> None:
    """Main function to run the bot."""
    # Register error handling middleware
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())

    # Register routers
    dp.include_routers(
        start.router,
        settings_handler.router,
        digest_handler.router,
        schedule_handler.router,
        library_handler.router,
        stats_handler.router,
    )

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}", exc_info=True)
