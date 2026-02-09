"""News Digest Bot - Main entry point."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from handlers import ErrorHandlingMiddleware
from handlers import start
from handlers import settings as settings_handler


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

    # TODO: Initialize db connection and start scheduler


async def on_shutdown() -> None:
    """Cleanup on bot shutdown."""
    logger.info("Shutting down News Digest Bot...")

    # TODO: Close db and gnews api connections and stop scheduler


async def main() -> None:
    """Main function to run the bot."""
    # Register error handling middleware
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())

    # Register routers
    dp.include_routers(
        start.router,
        settings_handler.router
    )

    # TODO: Register startup/shutdown handlers

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}", exc_info=True)
