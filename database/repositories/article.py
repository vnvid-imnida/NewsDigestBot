"""Article repository for database operations."""

from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Article


class ArticleRepository:
    """Repository for Article entity operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, article_id: uuid.UUID) -> Optional[Article]:
        """Get article by internal ID."""
        result = await self.session.execute(
            select(Article).where(Article.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Optional[Article]:
        """Get article by external ID (hash of URL)."""
        result = await self.session.execute(
            select(Article).where(Article.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        external_id: str,
        title: str,
        url: str,
        description: Optional[str] = None,
        source_name: Optional[str] = None,
        image_url: Optional[str] = None,
        published_at: Optional[str] = None,
    ) -> Article:
        """Create a new article."""
        from datetime import datetime

        pub_date = None
        if published_at:
            try:
                pub_date = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pub_date = datetime.now()

        article = Article(
            external_id=external_id,
            title=title,
            description=description,
            url=url,
            source_name=source_name,
            image_url=image_url,
            published_at=pub_date,
        )
        self.session.add(article)
        await self.session.flush()
        return article

    async def create_or_update(
        self,
        external_id: str,
        title: str,
        url: str,
        description: Optional[str] = None,
        source_name: Optional[str] = None,
        image_url: Optional[str] = None,
        published_at: Optional[str] = None,
    ) -> tuple[Article, bool]:
        """
        Create or update article by external_id.

        Returns:
            Tuple of (article, created) where created is True if new article was created.
        """
        from datetime import datetime

        existing = await self.get_by_external_id(external_id)
        if existing is not None:
            # Update existing article
            existing.title = title
            existing.description = description
            existing.url = url
            existing.source_name = source_name
            existing.image_url = image_url
            if published_at:
                try:
                    existing.published_at = datetime.fromisoformat(
                        published_at.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass
            await self.session.flush()
            return existing, False

        # Create new article
        article = await self.create(
            external_id=external_id,
            title=title,
            url=url,
            description=description,
            source_name=source_name,
            image_url=image_url,
            published_at=published_at,
        )
        return article, True

    async def get_many_by_external_ids(
        self, external_ids: List[str]
    ) -> List[Article]:
        """Get multiple articles by their external IDs."""
        if not external_ids:
            return []
        result = await self.session.execute(
            select(Article).where(Article.external_id.in_(external_ids))
        )
        return list(result.scalars().all())
