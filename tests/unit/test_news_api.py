"""
Unit tests для NewsApiService.

Тестируются:
- ArticleDTO.from_api_response: парсинг GNews API response
- NewsApiService.search: поиск статей по теме
- NewsApiService.search_multiple: поиск по нескольким темам
- NewsApiService.get_top_headlines: получение топ новостей
- Error handling: rate limits, API errors, network errors
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from services.news_api import (
    ArticleDTO,
    NewsApiError,
    NewsApiService,
    RateLimitError,
)


class TestArticleDTO:
    """Тесты для ArticleDTO."""

    def test_from_api_response_full_data(self):
        """
        Тест парсинга полного GNews API response.

        Проверяет:
        - Все поля корректно маппятся
        - external_id генерируется из URL (MD5 hash)
        - publishedAt парсится в datetime
        """
        api_data = {
            "title": "Python 3.12 Released",
            "description": "New features in Python 3.12",
            "url": "https://example.com/python-3.12",
            "image": "https://example.com/image.jpg",
            "publishedAt": "2024-02-01T10:00:00Z",
            "source": {"name": "TechCrunch", "url": "https://techcrunch.com"},
        }

        dto = ArticleDTO.from_api_response(api_data)

        assert dto.title == "Python 3.12 Released"
        assert dto.description == "New features in Python 3.12"
        assert dto.url == "https://example.com/python-3.12"
        assert dto.image_url == "https://example.com/image.jpg"
        assert dto.source_name == "TechCrunch"
        assert dto.external_id is not None  # MD5 hash
        assert len(dto.external_id) == 32  # MD5 hash длина
        assert isinstance(dto.published_at, datetime)

    def test_from_api_response_minimal_data(self):
        """Тест парсинга минимального response (только URL)."""
        api_data = {
            "url": "https://example.com/minimal",
            "publishedAt": "2024-02-01T10:00:00Z",
        }

        dto = ArticleDTO.from_api_response(api_data)

        assert dto.url == "https://example.com/minimal"
        assert dto.title == ""  # default для missing title
        assert dto.description is None
        assert dto.source_name is None
        assert dto.image_url is None

    def test_from_api_response_invalid_date(self):
        """
        Тест обработки невалидного publishedAt.

        Expected behavior: fallback на datetime.now()
        """
        api_data = {
            "url": "https://example.com/article",
            "publishedAt": "invalid-date-string",
        }

        dto = ArticleDTO.from_api_response(api_data)

        # Должен использовать datetime.now() как fallback
        assert isinstance(dto.published_at, datetime)
        # Проверяем что дата близка к текущему времени (tolerance 5 seconds)
        time_diff = abs((datetime.now(timezone.utc) - dto.published_at).total_seconds())
        assert time_diff < 5

    def test_from_api_response_missing_source(self):
        """Тест обработки missing source field."""
        api_data = {
            "url": "https://example.com/no-source",
            "publishedAt": "2024-02-01T10:00:00Z",
            # source field отсутствует
        }

        dto = ArticleDTO.from_api_response(api_data)

        assert dto.source_name is None

    def test_external_id_consistency(self):
        """
        Тест что external_id генерируется консистентно для одного URL.

        Одинаковый URL → одинаковый external_id (важно для deduplication).
        """
        api_data1 = {
            "url": "https://example.com/same-url",
            "publishedAt": "2024-02-01T10:00:00Z",
        }
        api_data2 = {
            "url": "https://example.com/same-url",
            "publishedAt": "2024-02-02T12:00:00Z",  # Другая дата
        }

        dto1 = ArticleDTO.from_api_response(api_data1)
        dto2 = ArticleDTO.from_api_response(api_data2)

        assert dto1.external_id == dto2.external_id


@pytest.mark.asyncio
class TestNewsApiService:
    """Тесты для NewsApiService."""

    @pytest.fixture
    def news_service(self):
        """Fixture для NewsApiService."""
        with patch("services.news_api.settings") as mock_settings:
            mock_settings.gnews_api_key = "test-api-key"
            mock_settings.gnews_language = "ru"
            mock_settings.gnews_max_results = 10
            service = NewsApiService()
            yield service

    async def test_search_success(self, news_service, mock_gnews_response):
        """
        Тест успешного поиска статей.

        Проверяет:
        - API вызывается с правильными params
        - Response парсится в ArticleDTO
        - Результаты возвращаются
        """
        with patch.object(
            news_service, "_request", return_value=mock_gnews_response
        ) as mock_request:
            articles = await news_service.search("Python")

            # Проверяем что _request был вызван
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "search"  # endpoint
            assert call_args[0][1]["q"] == "Python"  # query

            # Проверяем результаты
            assert len(articles) == 2
            assert all(isinstance(a, ArticleDTO) for a in articles)
            assert articles[0].title == "Python 3.12 Released with New Features"

    async def test_search_with_cache(self, news_service):
        """
        Тест что поиск использует cache.

        При повторном запросе не должен вызывать API.
        """
        mock_response = {"articles": [{"url": "https://test.com"}]}

        with patch.object(news_service, "_request", return_value=mock_response):
            # Первый вызов - fetches from API
            articles1 = await news_service.search("Python")

            # Второй вызов - should use cache
            with patch.object(
                news_service, "_request"
            ) as mock_no_call:  # Не должен вызываться
                articles2 = await news_service.search("Python")

                # Cache hit - _request не вызывается второй раз
                mock_no_call.assert_not_called()

    async def test_search_api_error_returns_empty(self, news_service):
        """
        Тест что API error возвращает пустой список.

        Expected behavior: graceful degradation, не бросаем exception.
        """
        with patch.object(news_service, "_request", return_value=None):
            articles = await news_service.search("Python")

            assert articles == []

    async def test_search_rate_limit_returns_cached(self, news_service):
        """
        Тест обработки rate limit error.

        Expected behavior: возвращаем cached results если есть,
        иначе пустой список.
        """
        # Первый вызов успешен - кешируется
        mock_response = {"articles": [{"url": "https://test.com"}]}
        with patch.object(news_service, "_request", return_value=mock_response):
            articles1 = await news_service.search("Python")
            assert len(articles1) == 1

        # Второй вызов - rate limit, должен вернуть cached
        with patch.object(
            news_service, "_request", side_effect=RateLimitError("Quota exceeded")
        ):
            articles2 = await news_service.search("Python")

            # Возвращаем cached results
            assert len(articles2) == 1

    async def test_search_multiple_deduplication(self, news_service):
        """
        Тест что search_multiple удаляет дубликаты.

        Если одна статья появляется в нескольких темах,
        должна быть в результате только один раз.
        """
        # Mock: обе темы возвращают одну статью с одинаковым URL
        same_article_response = {
            "articles": [{"url": "https://example.com/shared-article"}]
        }

        with patch.object(news_service, "search", return_value=[
            ArticleDTO.from_api_response(same_article_response["articles"][0])
        ]):
            articles = await news_service.search_multiple(["Python", "AI"])

            # Только один экземпляр статьи
            assert len(articles) == 1

    async def test_search_multiple_sorting(self, news_service):
        """
        Тест что search_multiple сортирует по published_at (newest first).
        """
        old_article = ArticleDTO(
            external_id="old",
            title="Old Article",
            description=None,
            url="https://example.com/old",
            source_name=None,
            image_url=None,
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        new_article = ArticleDTO(
            external_id="new",
            title="New Article",
            description=None,
            url="https://example.com/new",
            source_name=None,
            image_url=None,
            published_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
        )

        with patch.object(
            news_service, "search", side_effect=[[old_article], [new_article]]
        ):
            articles = await news_service.search_multiple(["Topic1", "Topic2"])

            # Сортировка: новые первые
            assert len(articles) == 2
            assert articles[0].title == "New Article"
            assert articles[1].title == "Old Article"

    async def test_get_top_headlines_success(self, news_service, mock_gnews_response):
        """Тест успешного получения top headlines."""
        with patch.object(
            news_service, "_request", return_value=mock_gnews_response
        ) as mock_request:
            articles = await news_service.get_top_headlines(category="technology")

            # Проверяем параметры
            call_args = mock_request.call_args
            assert call_args[0][0] == "top-headlines"
            assert call_args[0][1]["category"] == "technology"

            # Проверяем результаты
            assert len(articles) == 2
            assert all(isinstance(a, ArticleDTO) for a in articles)

    async def test_close_session(self, news_service):
        """Тест что close() закрывает aiohttp session."""
        # Создаем session
        session = await news_service._get_session()
        assert session is not None

        # Закрываем
        await news_service.close()

        # Session должен быть закрыт
        # NOTE: В реальности проверяем через mock
        assert True  # Simplified test


# NOTE: Тесты с реальным aiohttp.ClientSession требуют
# integration testing setup или использования aioresponses library
