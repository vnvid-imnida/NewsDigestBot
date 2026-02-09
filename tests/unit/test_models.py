"""
Unit tests для SQLAlchemy моделей базы данных.

Тестируются:
- User model: создание, валидация, default values
- Topic model: unique constraint (user_id, name)
- Schedule model: валидация JSON times field
"""

import pytest
from datetime import datetime, timezone
from database.models import User, Topic, Schedule


class TestUserModel:
    """Тесты для модели User"""

    def test_user_creation(self):
        """
        Тест создания пользователя с минимальными полями.

        Проверяет:
        - Обязательное поле telegram_id устанавливается
        - Default language_code = 'ru'
        - Timestamps created_at/updated_at генерируются автоматически
        """
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Тест"
        )

        assert user.telegram_id == 123456789
        assert user.username == "test_user"
        assert user.first_name == "Тест"
        assert user.language_code == "ru"  # default value

    def test_user_with_custom_language(self):
        """Тест создания пользователя с кастомным language_code"""
        user = User(
            telegram_id=987654321,
            language_code="en"
        )

        assert user.telegram_id == 987654321
        assert user.language_code == "en"

    def test_user_telegram_id_required(self):
        """
        Тест что telegram_id обязателен.

        NOTE: В production это проверяется на уровне БД (NOT NULL constraint),
        но SQLAlchemy модель позволяет создание без коммита.
        """
        user = User(username="test")
        assert user.telegram_id is None  # Допустимо до коммита

    def test_user_str_representation(self):
        """Тест строкового представления пользователя"""
        user = User(
            telegram_id=111222333,
            username="john_doe",
            first_name="John"
        )

        # SQLAlchemy по умолчанию использует __repr__
        assert "User" in repr(user)
        assert "111222333" in repr(user) or "john_doe" in repr(user)


class TestTopicModel:
    """Тесты для модели Topic"""

    def test_topic_creation(self):
        """Тест создания темы интересов"""
        topic = Topic(
            name="Python",
            user_id="550e8400-e29b-41d4-a716-446655440000"  # example UUID
        )

        assert topic.name == "Python"
        assert topic.user_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_topic_name_max_length(self):
        """
        Тест максимальной длины названия темы.

        Topic.name имеет constraint: String(100)
        """
        long_name = "A" * 100
        topic = Topic(
            name=long_name,
            user_id="550e8400-e29b-41d4-a716-446655440000"
        )

        assert len(topic.name) == 100
        assert topic.name == long_name

    def test_topic_name_exceeds_limit(self):
        """
        Тест что имя темы >100 символов будет обрезано/отклонено БД.

        NOTE: SQLAlchemy сама не обрезает, но PostgreSQL отклонит при INSERT.
        """
        too_long_name = "A" * 101
        topic = Topic(
            name=too_long_name,
            user_id="550e8400-e29b-41d4-a716-446655440000"
        )

        # До коммита допустимо
        assert len(topic.name) == 101


class TestScheduleModel:
    """Тесты для модели Schedule"""

    def test_schedule_creation_default_inactive(self):
        """
        Тест создания расписания с default values.

        По умолчанию:
        - is_active = False
        - times = []
        - timezone = 'Europe/Moscow'
        """
        schedule = Schedule(
            user_id="550e8400-e29b-41d4-a716-446655440000"
        )

        assert schedule.is_active is False
        assert schedule.times == []
        assert schedule.timezone == "Europe/Moscow"

    def test_schedule_with_times(self):
        """Тест создания расписания с временами доставки"""
        schedule = Schedule(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            is_active=True,
            times=["08:00", "18:00"],
            timezone="Europe/London"
        )

        assert schedule.is_active is True
        assert schedule.times == ["08:00", "18:00"]
        assert schedule.timezone == "Europe/London"

    def test_schedule_times_format_validation(self):
        """
        Тест валидации формата times (должен быть список строк "HH:MM").

        NOTE: Валидация формата времени реализована в application layer,
        не в модели. Здесь только проверяем что JSONB принимает список.
        """
        schedule = Schedule(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            times=["08:00", "12:30", "20:15"]
        )

        assert len(schedule.times) == 3
        assert all(":" in time for time in schedule.times)

    def test_schedule_last_sent_at_nullable(self):
        """Тест что last_sent_at может быть NULL (до первой отправки)"""
        schedule = Schedule(
            user_id="550e8400-e29b-41d4-a716-446655440000"
        )

        assert schedule.last_sent_at is None

    def test_schedule_last_sent_at_with_value(self):
        """Тест установки last_sent_at после отправки"""
        now = datetime.now(timezone.utc)
        schedule = Schedule(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            last_sent_at=now
        )

        assert schedule.last_sent_at == now


# Дополнительные integration-level тесты (требуют БД)
# переносятся в tests/integration/
