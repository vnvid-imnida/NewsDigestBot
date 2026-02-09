"""GNews.io API integration service."""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import aiohttp

from config.settings import settings
from utils.cache import articles_cache

logger = logging.getLogger(__name__)

GNEWS_BASE_URL = "https://gnews.io/api/v4"


@dataclass
class ArticleDTO:
    """Data transfer object for news articles."""

    external_id: str
    title: str
    description: Optional[str]
    url: str
    source_name: Optional[str]
    image_url: Optional[str]
    published_at: datetime

    @classmethod
    def from_api_response(cls, data: dict) -> "ArticleDTO":
        """Create ArticleDTO from GNews API response."""
        url = data.get("url", "")
        external_id = hashlib.md5(url.encode()).hexdigest()

        published_at_str = data.get("publishedAt", "")
        try:
            published_at = datetime.fromisoformat(
                published_at_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            published_at = datetime.now()

        source = data.get("source", {})

        return cls(
            external_id=external_id,
            title=data.get("title", ""),
            description=data.get("description"),
            url=url,
            source_name=source.get("name") if source else None,
            image_url=data.get("image"),
            published_at=published_at,
        )


class NewsApiError(Exception):
    """Base exception for News API errors."""

    pass


class RateLimitError(NewsApiError):
    """Raised when API rate limit is reached."""

    pass


class NewsApiService:
    """Service for interacting with GNews.io API."""

    def __init__(self):
        self.api_key = settings.gnews_api_key
        self.default_lang = settings.gnews_language
        self.max_results = settings.gnews_max_results
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self, endpoint: str, params: dict, retries: int = 3
    ) -> Optional[dict]:
        """Make API request with retry logic."""
        params["apikey"] = self.api_key
        url = f"{GNEWS_BASE_URL}/{endpoint}"

        for attempt in range(retries):
            try:
                session = await self._get_session()
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 403:
                        logger.warning("GNews API rate limit reached")
                        raise RateLimitError("Daily quota exceeded")
                    elif response.status == 400:
                        logger.error(f"GNews API bad request: {await response.text()}")
                        return None
                    else:
                        logger.error(
                            f"GNews API error: {response.status} - {await response.text()}"
                        )
                        if attempt < retries - 1:
                            await asyncio.sleep(2**attempt)  # Exponential backoff
                        continue
            except aiohttp.ClientError as e:
                logger.error(f"GNews API connection error: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2**attempt)
                continue

        return None

    async def search(
        self,
        query: str,
        lang: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[ArticleDTO]:
        """Search articles by query/topic."""
        cache_key = f"search:{query}:{lang or self.default_lang}"

        # Check cache first
        cached = articles_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for search: {query}")
            return cached

        params = {
            "q": query,
            "lang": lang or self.default_lang,
            "max": max_results or self.max_results,
        }

        try:
            data = await self._request("search", params)
            if data is None:
                return []

            articles = [
                ArticleDTO.from_api_response(article)
                for article in data.get("articles", [])
            ]

            # Cache results
            articles_cache.set(cache_key, articles)
            logger.info(f"Found {len(articles)} articles for query: {query}")
            return articles

        except RateLimitError:
            # Return cached if available, even if expired
            return cached if cached else []

    async def search_multiple(
        self,
        queries: List[str],
        lang: Optional[str] = None,
        max_per_query: int = 5,
    ) -> List[ArticleDTO]:
        """Search multiple topics and deduplicate results."""
        all_articles: List[ArticleDTO] = []
        seen_ids: set[str] = set()

        for query in queries:
            articles = await self.search(query, lang, max_per_query)
            for article in articles:
                if article.external_id not in seen_ids:
                    seen_ids.add(article.external_id)
                    all_articles.append(article)

        # Sort by published date (newest first)
        all_articles.sort(key=lambda a: a.published_at, reverse=True)
        return all_articles

    async def get_top_headlines(
        self,
        category: str = "general",
        country: str = "ru",
        lang: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[ArticleDTO]:
        """Get top headlines as fallback."""
        cache_key = f"headlines:{category}:{country}:{lang or self.default_lang}"

        # Check cache first
        cached = articles_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for headlines: {category}")
            return cached

        params = {
            "category": category,
            "country": country,
            "lang": lang or self.default_lang,
            "max": max_results or self.max_results,
        }

        try:
            data = await self._request("top-headlines", params)
            if data is None:
                return []

            articles = [
                ArticleDTO.from_api_response(article)
                for article in data.get("articles", [])
            ]

            # Cache results
            articles_cache.set(cache_key, articles)
            logger.info(f"Found {len(articles)} headlines for category: {category}")
            return articles

        except RateLimitError:
            return cached if cached else []


# Singleton instance
news_api_service = NewsApiService()
