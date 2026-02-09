"""
Shared pytest fixtures для всех тестов.

Fixtures:
- mock_db_session: Mocked SQLAlchemy async session
- sample_user: Fixture для тестового пользователя
- sample_article: Fixture для тестовой статьи
- mock_news_api: Mock для NewsApiService
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from database.models import Article, User
from services.news_api import ArticleDTO


@pytest.fixture
def sample_user_data():
    """Данные для создания тестового пользователя."""
    return {
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Тест",
        "language_code": "ru",
    }


@pytest.fixture
def sample_user(sample_user_data):
    """Fixture для тестового пользователя."""
    return User(
        id=uuid.uuid4(),
        telegram_id=sample_user_data["telegram_id"],
        username=sample_user_data["username"],
        first_name=sample_user_data["first_name"],
        language_code=sample_user_data["language_code"],
    )


@pytest.fixture
def sample_article_data():
    """Данные для создания тестовой статьи."""
    return {
        "external_id": "abc123def456",
        "title": "Test Article Title",
        "description": "Test article description",
        "url": "https://example.com/article",
        "source_name": "Test Source",
        "image_url": "https://example.com/image.jpg",
        "published_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_article(sample_article_data):
    """Fixture для тестовой статьи."""
    return Article(
        id=uuid.uuid4(),
        external_id=sample_article_data["external_id"],
        title=sample_article_data["title"],
        description=sample_article_data["description"],
        url=sample_article_data["url"],
        source_name=sample_article_data["source_name"],
        image_url=sample_article_data["image_url"],
        published_at=sample_article_data["published_at"],
    )


@pytest.fixture
def sample_article_dto(sample_article_data):
    """Fixture для ArticleDTO."""
    return ArticleDTO(
        external_id=sample_article_data["external_id"],
        title=sample_article_data["title"],
        description=sample_article_data["description"],
        url=sample_article_data["url"],
        source_name=sample_article_data["source_name"],
        image_url=sample_article_data["image_url"],
        published_at=sample_article_data["published_at"],
    )


@pytest.fixture
async def mock_db_session():
    """
    Mock для SQLAlchemy async session.

    NOTE: Для реальных integration тестов использовать testcontainers
    или отдельную test database.
    """
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    return session


@pytest.fixture
def mock_news_api():
    """Mock для NewsApiService."""
    api = AsyncMock()
    api.search = AsyncMock(return_value=[])
    api.search_multiple = AsyncMock(return_value=[])
    api.get_top_headlines = AsyncMock(return_value=[])
    api.close = AsyncMock()
    return api


@pytest.fixture
def mock_gnews_response():
    """Mock GNews API response."""
    return {
        "totalArticles": 2,
        "articles": [
            {
                "title": "Python 3.12 Released with New Features",
                "description": "Python 3.12 introduces improved performance...",
                "url": "https://example.com/python-3.12",
                "image": "https://example.com/python-image.jpg",
                "publishedAt": "2024-02-01T10:00:00Z",
                "source": {"name": "TechCrunch", "url": "https://techcrunch.com"},
            },
            {
                "title": "AI Breakthrough in NLP",
                "description": "Researchers have achieved...",
                "url": "https://example.com/ai-nlp",
                "image": "https://example.com/ai-image.jpg",
                "publishedAt": "2024-02-01T12:00:00Z",
                "source": {"name": "MIT News", "url": "https://news.mit.edu"},
            },
        ],
    }


@pytest.fixture
def mock_telegram_message():
    """Mock Telegram Message object."""
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = 123456789
    message.from_user.username = "test_user"
    message.from_user.first_name = "Тест"
    message.from_user.language_code = "ru"
    message.chat = MagicMock()
    message.chat.id = 123456789
    message.text = "/start"
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    return message


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram Bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.edit_message_text = AsyncMock()
    return bot
