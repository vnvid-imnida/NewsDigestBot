"""Topic repository for database operations."""

from typing import List, Optional
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Topic, User


class TopicRepository:
    """Repository for Topic entity operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, name: str) -> Topic:
        """Create a new topic for user."""
        # Normalize topic name
        normalized_name = name.strip().lower()

        topic = Topic(user_id=user_id, name=normalized_name)
        self.session.add(topic)
        await self.session.flush()
        return topic

    async def get_by_id(self, topic_id: uuid.UUID) -> Optional[Topic]:
        """Get topic by ID."""
        result = await self.session.execute(select(Topic).where(Topic.id == topic_id))
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> List[Topic]:
        """Get all topics for a user."""
        result = await self.session.execute(
            select(Topic)
            .where(Topic.user_id == user_id)
            .order_by(Topic.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_by_telegram_id(self, telegram_id: int) -> List[Topic]:
        """Get all topics for a user by Telegram ID."""
        result = await self.session.execute(
            select(Topic)
            .join(User)
            .where(User.telegram_id == telegram_id)
            .order_by(Topic.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        """Count topics for a user."""
        result = await self.session.execute(
            select(func.count(Topic.id)).where(Topic.user_id == user_id)
        )
        return result.scalar_one()

    async def delete(self, topic_id: uuid.UUID) -> bool:
        """Delete a topic by ID."""
        result = await self.session.execute(
            delete(Topic).where(Topic.id == topic_id)
        )
        return result.rowcount > 0

    async def delete_all_by_user(self, user_id: uuid.UUID) -> int:
        """Delete all topics for a user."""
        result = await self.session.execute(
            delete(Topic).where(Topic.user_id == user_id)
        )
        return result.rowcount

    async def exists(self, user_id: uuid.UUID, name: str) -> bool:
        """Check if topic with given name exists for user."""
        normalized_name = name.strip().lower()
        result = await self.session.execute(
            select(func.count(Topic.id)).where(
                Topic.user_id == user_id, Topic.name == normalized_name
            )
        )
        return result.scalar_one() > 0

    async def replace_all(self, user_id: uuid.UUID, names: List[str]) -> List[Topic]:
        """Replace all user topics with new list."""
        # Delete existing topics
        await self.delete_all_by_user(user_id)

        # Create new topics
        topics = []
        for name in names:
            topic = await self.create(user_id, name)
            topics.append(topic)

        return topics
