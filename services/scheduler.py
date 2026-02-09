"""APScheduler service for scheduled digest delivery."""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import settings
from database.connection import get_session
from database.repositories.schedule import ScheduleRepository
from services.digest import digest_service
from texts.schedule import LOG_SCHEDULED_DIGEST_SENT

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=settings.timezone)
    return _scheduler


async def send_scheduled_digest(bot, telegram_id: int) -> bool:
    """
    Send scheduled digest to user.

    Args:
        bot: Aiogram Bot instance
        telegram_id: User's Telegram ID

    Returns:
        True if digest was sent successfully
    """
    try:
        # Generate digest
        result = await digest_service.generate_digest(telegram_id)

        if result.error or not result.articles:
            logger.debug(f"No digest to send for user {telegram_id}: {result.error}")
            return False

        # Format message
        digest_text = digest_service.format_digest_message(result)

        # Send to user
        await bot.send_message(
            chat_id=telegram_id,
            text=digest_text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

        logger.info(LOG_SCHEDULED_DIGEST_SENT.format(telegram_id=telegram_id))
        return True

    except Exception as e:
        logger.error(f"Error sending scheduled digest to {telegram_id}: {e}")
        return False


async def check_and_send_digests(bot) -> None:
    """
    Check all schedules and send digests where needed.

    This is the main job that runs every minute.
    """
    current_time = datetime.now().strftime("%H:%M")
    logger.debug(f"Checking schedules for time {current_time}")

    try:
        async with get_session() as session:
            schedule_repo = ScheduleRepository(session)
            schedules = await schedule_repo.get_schedules_for_time(current_time)

            if not schedules:
                return

            logger.info(f"Found {len(schedules)} schedules to process for {current_time}")

            for schedule, user in schedules:
                await send_scheduled_digest(bot, user.telegram_id)

    except Exception as e:
        logger.error(f"Error in scheduled digest check: {e}")


def setup_scheduler(bot) -> AsyncIOScheduler:
    """
    Set up and configure the scheduler.

    Args:
        bot: Aiogram Bot instance

    Returns:
        Configured scheduler instance
    """
    scheduler = get_scheduler()

    # Add main job - runs every minute to check schedules
    scheduler.add_job(
        check_and_send_digests,
        CronTrigger(minute="*"),  # Every minute
        args=[bot],
        id="check_digests",
        replace_existing=True,
        misfire_grace_time=60,
    )

    logger.info("Scheduler configured with digest check job")
    return scheduler


async def start_scheduler(bot) -> None:
    """Start the scheduler."""
    scheduler = setup_scheduler(bot)
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


async def stop_scheduler() -> None:
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
        _scheduler = None
