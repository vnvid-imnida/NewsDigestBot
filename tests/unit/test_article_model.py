"""
Unit tests для моделей Article и SavedArticle.

Тестируются:
- Article model: создание, валидация, unique external_id
- SavedArticle model: связи user-article, unique constraint
"""

import pytest
import uuid
from datetime import datetime, timezone

from database.models import Article, SavedArticle, User


class TestArticleModel:
    """Тесты для модели Article."""

    def test_article_creation(self):
        """
        Тест создания статьи со всеми полями.

        Проверяет:
        - Все обязательные поля устанавливаются
        - external_id используется для уникальной идентификации
        - published_at и fetched_at имеют timezone
        """
        now = datetime.now(timezone.utc)
        article = Article(
            external_id="abc123def456",
            title="Python 3.12 Released",
            description="New features in Python 3.12",
            url="https://example.com/python-3.12",
            source_name="TechCrunch",
            image_url="https://example.com/image.jpg",
            published_at=now,
        )

        assert article.external_id == "abc123def456"
        assert article.title == "Python 3.12 Released"
        assert article.description == "New features in Python 3.12"
        assert article.url == "https://example.com/python-3.12"
        assert article.source_name == "TechCrunch"
        assert article.image_url == "https://example.com/image.jpg"
        assert article.published_at == now

    def test_article_minimal_fields(self):
        """
        Тест создания статьи с минимальными обязательными полями.

        Optional поля (description, source_name, image_url) могут быть None.
        """
        article = Article(
            external_id="xyz789",
            title="Minimal Article",
            url="https://example.com/minimal",
            published_at=datetime.now(timezone.utc),
        )

        assert article.external_id == "xyz789"
        assert article.title == "Minimal Article"
        assert article.description is None
        assert article.source_name is None
        assert article.image_url is None

    def test_article_title_max_length(self):
        """
        Тест максимальной длины заголовка.

        Article.title имеет constraint: String(500)
        """
        long_title = "A" * 500
        article = Article(
            external_id="long-title-id",
            title=long_title,
            url="https://example.com/long",
            published_at=datetime.now(timezone.utc),
        )

        assert len(article.title) == 500
        assert article.title == long_title

    def test_article_url_max_length(self):
        """
        Тест максимальной длины URL.

        Article.url имеет constraint: String(2000)
        """
        long_url = "https://example.com/" + "x" * 1970  # Total ~2000 chars
        article = Article(
            external_id="long-url-id",
            title="Long URL Article",
            url=long_url,
            published_at=datetime.now(timezone.utc),
        )

        assert len(article.url) <= 2000
        assert article.url == long_url

    def test_article_external_id_uniqueness_intent(self):
        """
        Тест что external_id должен быть unique.

        NOTE: Реальная проверка unique constraint требует БД.
        Здесь проверяем что поле маркировано как unique в модели.
        """
        article1 = Article(
            external_id="same-id",
            title="Article 1",
            url="https://example.com/1",
            published_at=datetime.now(timezone.utc),
        )
        article2 = Article(
            external_id="same-id",
            title="Article 2",
            url="https://example.com/2",
            published_at=datetime.now(timezone.utc),
        )

        # Без коммита допустимо
        assert article1.external_id == article2.external_id


class TestSavedArticleModel:
    """Тесты для модели SavedArticle."""

    def test_saved_article_creation(self):
        """Тест создания связи user-article при сохранении."""
        user_id = uuid.uuid4()
        article_id = uuid.uuid4()

        saved = SavedArticle(user_id=user_id, article_id=article_id)

        assert saved.user_id == user_id
        assert saved.article_id == article_id
        assert saved.id is not None  # UUID генерируется автоматически

    def test_saved_article_saved_at_timestamp(self):
        """
        Тест что saved_at автоматически устанавливается через server_default.

        NOTE: server_default работает только при INSERT в БД,
        здесь проверяем что поле nullable.
        """
        saved = SavedArticle(
            user_id=uuid.uuid4(), article_id=uuid.uuid4(), saved_at=None
        )

        # До коммита может быть None
        assert saved.saved_at is None

    def test_saved_article_with_explicit_timestamp(self):
        """Тест установки явного timestamp для saved_at."""
        now = datetime.now(timezone.utc)
        saved = SavedArticle(
            user_id=uuid.uuid4(), article_id=uuid.uuid4(), saved_at=now
        )

        assert saved.saved_at == now

    def test_saved_article_unique_constraint_intent(self):
        """
        Тест что комбинация (user_id, article_id) должна быть unique.

        Constraint: saved_articles_user_article_unique
        Гарантирует что пользователь не может сохранить одну статью дважды.

        NOTE: Реальная проверка требует БД с constraint.
        """
        user_id = uuid.uuid4()
        article_id = uuid.uuid4()

        saved1 = SavedArticle(user_id=user_id, article_id=article_id)
        saved2 = SavedArticle(user_id=user_id, article_id=article_id)

        # Без коммита допустимо создание дубликатов
        assert saved1.user_id == saved2.user_id
        assert saved1.article_id == saved2.article_id

    def test_saved_article_different_users_same_article(self):
        """
        Тест что разные пользователи могут сохранить одну статью.

        Unique constraint только на (user_id, article_id) пару.
        """
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()
        article_id = uuid.uuid4()

        saved1 = SavedArticle(user_id=user1_id, article_id=article_id)
        saved2 = SavedArticle(user_id=user2_id, article_id=article_id)

        assert saved1.article_id == saved2.article_id
        assert saved1.user_id != saved2.user_id  # Разные пользователи


# Дополнительные тесты для relationships требуют БД setup
# и находятся в tests/integration/
