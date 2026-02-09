"""Digest generation service."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from database.connection import get_session
from database.repositories.topic import TopicRepository
from database.repositories.user import UserRepository
from services.news_api import ArticleDTO, NewsApiService, news_api_service, RateLimitError
from utils.cache import digest_cache

logger = logging.getLogger(__name__)


@dataclass
class DigestResult:
    """Result of digest generation."""

    articles: List[ArticleDTO]
    topics: List[str]
    from_cache: bool = False
    error: Optional[str] = None


class DigestService:
    """Service for generating personalized news digests."""

    def __init__(self, news_api: NewsApiService):
        self.news_api = news_api

    async def generate_digest(
        self,
        telegram_id: int,
        max_articles: int = 10,
        max_per_topic: int = 5,
    ) -> DigestResult:
        """
        Generate a personalized digest for user.

        Args:
            telegram_id: User's Telegram ID
            max_articles: Maximum total articles to return
            max_per_topic: Maximum articles per topic

        Returns:
            DigestResult with articles and metadata
        """
        # Check cache first
        cache_key = f"digest:{telegram_id}"
        cached = digest_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for digest: {telegram_id}")
            cached.from_cache = True
            return cached

        # Get user's topics from database
        topics = []
        try:
            async with get_session() as session:
                topic_repo = TopicRepository(session)
                db_topics = await topic_repo.list_by_telegram_id(telegram_id)
                topics = [t.name for t in db_topics]
        except Exception as e:
            logger.error(f"Error loading topics for user {telegram_id}: {e}")
            return DigestResult(
                articles=[],
                topics=[],
                error="database_error"
            )

        if not topics:
            logger.info(f"No topics configured for user {telegram_id}")
            return DigestResult(
                articles=[],
                topics=[],
                error="no_topics"
            )

        # Fetch news for all topics
        try:
            articles = await self.news_api.search_multiple(
                queries=topics,
                max_per_query=max_per_topic,
            )

            # Limit total articles
            articles = articles[:max_articles]

            result = DigestResult(
                articles=articles,
                topics=topics,
            )

            # Cache the result
            digest_cache.set(cache_key, result)

            logger.info(
                f"Generated digest with {len(articles)} articles "
                f"for user {telegram_id} (topics: {topics})"
            )

            return result

        except RateLimitError:
            logger.warning(f"Rate limit reached for user {telegram_id}")
            # Try to return cached result even if expired
            if cached:
                cached.from_cache = True
                return cached
            return DigestResult(
                articles=[],
                topics=topics,
                error="rate_limit"
            )
        except Exception as e:
            logger.error(f"Error fetching news for user {telegram_id}: {e}")
            return DigestResult(
                articles=[],
                topics=topics,
                error="api_error"
            )

    def format_time_ago(self, dt: datetime) -> str:
        """Format datetime as 'time ago' string."""
        now = datetime.now(timezone.utc)

        # Make dt timezone-aware if it isn't
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        diff = now - dt
        seconds = int(diff.total_seconds())

        if seconds < 60:
            return "только что"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} мин. назад"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} ч. назад"
        elif seconds < 604800:
            days = seconds // 86400
            return f"{days} дн. назад"
        else:
            return dt.strftime("%d.%m.%Y")

    def format_digest_message(
        self,
        result: DigestResult,
        show_descriptions: bool = True,
    ) -> str:
        """
        Format digest result as a Telegram message.

        Args:
            result: DigestResult from generate_digest
            show_descriptions: Whether to show article descriptions

        Returns:
            Formatted message string
        """
        from texts.digest import (
            DIGEST_HEADER,
            DIGEST_TOPICS_HEADER,
            ARTICLE_FORMAT,
            ARTICLE_FORMAT_SHORT,
            ARTICLE_SEPARATOR,
            DIGEST_FOOTER,
        )

        if not result.articles:
            return ""

        parts = [DIGEST_HEADER]

        # Add topics
        if result.topics:
            topics_str = ", ".join(result.topics[:5])
            if len(result.topics) > 5:
                topics_str += f" (+{len(result.topics) - 5})"
            parts.append(DIGEST_TOPICS_HEADER.format(topics=topics_str))

        # Add articles
        for i, article in enumerate(result.articles):
            time_ago = self.format_time_ago(article.published_at)
            source = article.source_name or "Источник"

            # Escape special characters for Markdown
            title = self._escape_markdown(article.title)
            description = ""
            if show_descriptions and article.description:
                description = self._escape_markdown(article.description[:200])
                if len(article.description) > 200:
                    description += "..."

            if show_descriptions and description:
                article_text = ARTICLE_FORMAT.format(
                    title=title,
                    description=description,
                    source=source,
                    time_ago=time_ago,
                    url=article.url,
                )
            else:
                article_text = ARTICLE_FORMAT_SHORT.format(
                    title=title,
                    source=source,
                    time_ago=time_ago,
                    url=article.url,
                )

            parts.append(f"{i + 1}. {article_text}")

            if i < len(result.articles) - 1:
                parts.append(ARTICLE_SEPARATOR)

        parts.append(DIGEST_FOOTER)

        return "".join(parts)

    def _escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters."""
        # Characters that need escaping in Markdown
        special_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text


# Singleton instance
digest_service = DigestService(news_api_service)
