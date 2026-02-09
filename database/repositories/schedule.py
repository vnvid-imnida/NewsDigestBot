"""Schedule repository for database operations."""

from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Schedule, User


class ScheduleRepository:
    """Repository for Schedule entity operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(self, user_id: uuid.UUID) -> Optional[Schedule]:
        """Get schedule for user."""
        result = await self.session.execute(
            select(Schedule).where(Schedule.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Schedule]:
        """Get schedule by user's Telegram ID."""
        result = await self.session.execute(
            select(Schedule)
            .join(User)
            .where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        times: List[str],
        timezone: str = "Europe/Moscow",
        is_active: bool = True,
    ) -> Schedule:
        """Create a new schedule for user."""
        schedule = Schedule(
            user_id=user_id,
            times=times,
            timezone=timezone,
            is_active=is_active,
        )
        self.session.add(schedule)
        await self.session.flush()
        return schedule

    async def create_or_update(
        self,
        user_id: uuid.UUID,
        times: List[str],
        timezone: str = "Europe/Moscow",
        is_active: bool = True,
    ) -> tuple[Schedule, bool]:
        """
        Create or update schedule for user.

        Returns:
            Tuple of (schedule, created) where created is True if new schedule was created.
        """
        existing = await self.get_by_user(user_id)
        if existing is not None:
            existing.times = times
            existing.timezone = timezone
            existing.is_active = is_active
            await self.session.flush()
            return existing, False

        schedule = await self.create(
            user_id=user_id,
            times=times,
            timezone=timezone,
            is_active=is_active,
        )
        return schedule, True

    async def update_times(
        self,
        user_id: uuid.UUID,
        times: List[str],
    ) -> Optional[Schedule]:
        """Update schedule times for user."""
        schedule = await self.get_by_user(user_id)
        if schedule is None:
            return None
        schedule.times = times
        await self.session.flush()
        return schedule

    async def toggle_active(self, user_id: uuid.UUID) -> Optional[Schedule]:
        """Toggle schedule active status for user."""
        schedule = await self.get_by_user(user_id)
        if schedule is None:
            return None
        schedule.is_active = not schedule.is_active
        await self.session.flush()
        return schedule

    async def set_active(
        self,
        user_id: uuid.UUID,
        is_active: bool,
    ) -> Optional[Schedule]:
        """Set schedule active status for user."""
        schedule = await self.get_by_user(user_id)
        if schedule is None:
            return None
        schedule.is_active = is_active
        await self.session.flush()
        return schedule

    async def get_active_schedules(self) -> List[tuple[Schedule, User]]:
        """Get all active schedules with their users."""
        result = await self.session.execute(
            select(Schedule, User)
            .join(User)
            .where(Schedule.is_active == True)  # noqa: E712
        )
        return list(result.all())

    async def get_schedules_for_time(self, time_str: str) -> List[tuple[Schedule, User]]:
        """
        Get all active schedules that should run at given time.

        Args:
            time_str: Time in HH:MM format
        """
        # JSONB contains check for the time
        result = await self.session.execute(
            select(Schedule, User)
            .join(User)
            .where(
                Schedule.is_active == True,  # noqa: E712
                Schedule.times.contains([time_str]),
            )
        )
        return list(result.all())
