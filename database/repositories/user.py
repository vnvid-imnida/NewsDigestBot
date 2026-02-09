"""User repository for database operations."""

from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


class UserRepository:
    """Repository for User entity operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by internal ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        language_code: str = "ru",
    ) -> tuple[User, bool]:
        """
        Get existing user or create a new one.

        Returns:
            Tuple of (user, created) where created is True if new user was created.
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user is not None:
            # Update user info if changed
            updated = False
            if username is not None and user.username != username:
                user.username = username
                updated = True
            if first_name is not None and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if language_code and user.language_code != language_code:
                user.language_code = language_code
                updated = True
            if updated:
                await self.session.flush()
            return user, False

        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language_code=language_code,
        )
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def update(self, user: User) -> User:
        """Update user in database."""
        await self.session.flush()
        return user
