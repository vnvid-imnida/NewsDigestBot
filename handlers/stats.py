"""Stats handler for /stats command."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Router, types, F
from aiogram.filters import Command

from database.connection import get_session
from database.repositories.user import UserRepository
from database.repositories.topic import TopicRepository
from database.repositories.library import LibraryRepository
from database.repositories.schedule import ScheduleRepository
from keyboards import main_menu
from texts.stats import (
    STATS_MESSAGE_TEMPLATE,
    SCHEDULE_ACTIVE,
    SCHEDULE_PAUSED,
    SCHEDULE_NOT_SET,
    SCHEDULE_DETAILS_TEMPLATE,
    USER_NOT_FOUND_ERROR,
    STATS_LOAD_ERROR,
    LOG_STATS_VIEWED,
    LOG_STATS_ERROR,
    LOG_USER_NOT_FOUND,
)
from texts.start import STATS

logger = logging.getLogger(__name__)
router = Router()

# Moscow timezone for date formatting
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def format_registration_date(dt: datetime) -> str:
    """Format registration date as 'DD.MM.YYYY в HH:MM'."""
    return dt.strftime("%d.%m.%Y в %H:%M")


def format_last_sent(dt: datetime) -> str:
    """
    Format last sent datetime with relative dates.
    Returns 'сегодня в HH:MM', 'вчера в HH:MM' or 'DD.MM.YYYY в HH:MM'.
    """
    now = datetime.now(dt.tzinfo)
    today = now.date()
    yesterday = today - timedelta(days=1)
    sent_date = dt.date()

    time_str = dt.strftime("%H:%M")

    if sent_date == today:
        return f"сегодня в {time_str}"
    elif sent_date == yesterday:
        return f"вчера в {time_str}"
    else:
        return dt.strftime(f"%d.%m.%Y в {time_str}")


@router.message(Command("stats"))
@router.message(F.text == STATS)
async def cmd_stats(message: types.Message):
    """
    Handle /stats command and stats button - show user statistics.
    """
    telegram_id = message.from_user.id

    try:
        async with get_session() as session:
            # Get user
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)

            if user is None:
                logger.warning(LOG_USER_NOT_FOUND.format(telegram_id=telegram_id))
                await message.answer(
                    USER_NOT_FOUND_ERROR,
                    reply_markup=main_menu.get_main_keyboard(),
                )
                return

            # Get topics count
            topic_repo = TopicRepository(session)
            topics_count = await topic_repo.count_by_user(user.id)

            # Get saved articles count
            library_repo = LibraryRepository(session)
            saved_articles_count = await library_repo.count_by_user(user.id)

            # Get schedule
            schedule_repo = ScheduleRepository(session)
            schedule = await schedule_repo.get_by_user(user.id)

            # Convert registration date to Moscow timezone
            created_at_msk = user.created_at.astimezone(MOSCOW_TZ)
            registration_date = format_registration_date(created_at_msk)

            # Determine schedule status and details
            if schedule is None:
                schedule_status = SCHEDULE_NOT_SET
                schedule_details = ""
            elif schedule.is_active:
                schedule_status = SCHEDULE_ACTIVE
                times_str = ", ".join(schedule.times)

                # Format last sent if exists
                if schedule.last_sent_at:
                    last_sent_msk = schedule.last_sent_at.astimezone(MOSCOW_TZ)
                    last_sent_str = format_last_sent(last_sent_msk)
                else:
                    last_sent_str = "—"

                schedule_details = SCHEDULE_DETAILS_TEMPLATE.format(
                    times=times_str,
                    last_sent=last_sent_str,
                )
            else:
                schedule_status = SCHEDULE_PAUSED
                schedule_details = ""

            # Build final message
            stats_message = STATS_MESSAGE_TEMPLATE.format(
                registration_date=registration_date,
                topics_count=topics_count,
                saved_articles_count=saved_articles_count,
                schedule_status=schedule_status,
                schedule_details=schedule_details,
            )

            # Send message
            await message.answer(
                stats_message,
                reply_markup=main_menu.get_main_keyboard(),
            )

            # Log successful view
            logger.info(
                LOG_STATS_VIEWED.format(
                    user_id=user.id,
                    telegram_id=telegram_id,
                )
            )

    except Exception:
        logger.exception(LOG_STATS_ERROR.format(telegram_id=telegram_id))
        await message.answer(
            STATS_LOAD_ERROR,
            reply_markup=main_menu.get_main_keyboard(),
        )
