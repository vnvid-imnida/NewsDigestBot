"""Library repository for saved articles operations."""

from typing import List, Optional, Set
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Article, SavedArticle


class LibraryRepository:
    """Repository for SavedArticle (library) operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_article(
        self,
        user_id: uuid.UUID,
        article_id: uuid.UUID,
    ) -> SavedArticle:
        """Save article to user's library."""
        saved = SavedArticle(user_id=user_id, article_id=article_id)
        self.session.add(saved)
        await self.session.flush()
        return saved

    async def is_saved(
        self,
        user_id: uuid.UUID,
        external_id: str,
    ) -> bool:
        """Check if article is saved in user's library by external_id."""
        result = await self.session.execute(
            select(func.count(SavedArticle.id))
            .join(Article)
            .where(
                SavedArticle.user_id == user_id,
                Article.external_id == external_id,
            )
        )
        return result.scalar_one() > 0

    async def is_saved_by_article_id(
        self,
        user_id: uuid.UUID,
        article_id: uuid.UUID,
    ) -> bool:
        """Check if article is saved in user's library by article_id."""
        result = await self.session.execute(
            select(func.count(SavedArticle.id)).where(
                SavedArticle.user_id == user_id,
                SavedArticle.article_id == article_id,
            )
        )
        return result.scalar_one() > 0

    async def get_saved_external_ids(
        self,
        user_id: uuid.UUID,
        external_ids: List[str],
    ) -> Set[str]:
        """Get set of external_ids that are saved for user."""
        if not external_ids:
            return set()

        result = await self.session.execute(
            select(Article.external_id)
            .join(SavedArticle)
            .where(
                SavedArticle.user_id == user_id,
                Article.external_id.in_(external_ids),
            )
        )
        return set(result.scalars().all())

    async def delete_saved(
        self,
        user_id: uuid.UUID,
        article_id: uuid.UUID,
    ) -> bool:
        """Remove article from user's library."""
        result = await self.session.execute(
            delete(SavedArticle).where(
                SavedArticle.user_id == user_id,
                SavedArticle.article_id == article_id,
            )
        )
        return result.rowcount > 0

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> List[tuple[SavedArticle, Article]]:
        """
        Get saved articles for user with pagination.

        Returns list of (SavedArticle, Article) tuples ordered by saved_at DESC.
        """
        result = await self.session.execute(
            select(SavedArticle, Article)
            .join(Article)
            .where(SavedArticle.user_id == user_id)
            .order_by(SavedArticle.saved_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        """Count saved articles for user."""
        result = await self.session.execute(
            select(func.count(SavedArticle.id)).where(
                SavedArticle.user_id == user_id
            )
        )
        return result.scalar_one()
