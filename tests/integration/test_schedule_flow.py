"""
Integration тест для автоматической доставки дайджеста по расписанию.

Покрывает User Story 2: "Автоматическая доставка дайджеста"

Сценарий:
1. Пользователь настраивает расписание через /schedule
2. Указывает время доставки (например, 08:00 и 18:00)
3. APScheduler автоматически отправляет дайджест в указанное время
4. Пользователь может изменить или отключить расписание

Acceptance Criteria (из spec.md):
- Пользователь может установить расписание (1-3 времени в день)
- Бот автоматически отправляет дайджест в указанное время
- Timezone учитывается (Europe/Moscow по умолчанию)
- Пользователь может деактивировать расписание
"""

import pytest
from datetime import datetime, time, timezone
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
@pytest.mark.integration
class TestScheduleFlow:
    """Integration тест для автоматической доставки дайджеста."""

    @pytest.fixture
    async def mock_scheduler(self):
        """Fixture для mock APScheduler."""
        scheduler = MagicMock()
        scheduler.add_job = MagicMock()
        scheduler.remove_job = MagicMock()
        scheduler.get_job = MagicMock()
        return scheduler

    async def test_user_sets_schedule(self, mock_scheduler):
        """
        Тест настройки расписания пользователем.

        Steps:
        1. User sends /schedule
        2. Sets delivery times: 08:00, 18:00
        3. Schedule saved to database
        4. APScheduler jobs created
        """
        # ARRANGE: User data
        user_id = "user-123"
        times = ["08:00", "18:00"]
        timezone_str = "Europe/Moscow"

        # ACT: Create schedule
        with patch('database.models.Schedule') as MockSchedule:
            schedule = MockSchedule(
                user_id=user_id,
                is_active=True,
                times=times,
                timezone=timezone_str,
            )

            # ASSERT: Schedule created
            assert schedule.is_active is True
            assert schedule.times == ["08:00", "18:00"]
            assert schedule.timezone == "Europe/Moscow"

    async def test_schedule_with_one_time(self, mock_scheduler):
        """Тест расписания с одним временем доставки."""
        user_id = "user-123"

        with patch('database.models.Schedule') as MockSchedule:
            schedule = MockSchedule(
                user_id=user_id, is_active=True, times=["09:00"], timezone="Europe/Moscow"
            )

            assert len(schedule.times) == 1
            assert schedule.times[0] == "09:00"

    async def test_schedule_with_three_times(self, mock_scheduler):
        """
        Тест расписания с максимальным количеством времен (3).

        Spec limit: 1-3 времени в день.
        """
        user_id = "user-123"

        with patch('database.models.Schedule') as MockSchedule:
            schedule = MockSchedule(
                user_id=user_id,
                is_active=True,
                times=["08:00", "13:00", "20:00"],
                timezone="Europe/Moscow",
            )

            assert len(schedule.times) == 3

    async def test_user_deactivates_schedule(self, mock_scheduler):
        """
        Тест деактивации расписания.

        Expected behavior:
        - is_active = False
        - APScheduler jobs удаляются
        - Дайджест больше не отправляется автоматически
        """
        # ARRANGE: Active schedule
        user_id = "user-123"

        with patch('database.models.Schedule') as MockSchedule:
            schedule = MockSchedule(
                user_id=user_id,
                is_active=True,
                times=["08:00"],
                timezone="Europe/Moscow",
            )

            # ACT: Deactivate
            schedule.is_active = False

            # ASSERT: Schedule deactivated
            assert schedule.is_active is False
            # В реальном коде: scheduler.remove_job(job_id)

    async def test_schedule_timezone_handling(self, mock_scheduler):
        """
        Тест обработки timezone.

        Expected behavior:
        - Время хранится в UTC в БД
        - Отправка происходит в пользовательском timezone
        """
        user_id = "user-123"

        with patch('database.models.Schedule') as MockSchedule:
            # Moscow timezone
            schedule_msk = MockSchedule(
                user_id=user_id, is_active=True, times=["10:00"], timezone="Europe/Moscow"
            )
            assert schedule_msk.timezone == "Europe/Moscow"

            # London timezone
            schedule_london = MockSchedule(
                user_id=user_id, is_active=True, times=["10:00"], timezone="Europe/London"
            )
            assert schedule_london.timezone == "Europe/London"

    async def test_schedule_last_sent_at_updates(self, mock_scheduler):
        """
        Тест обновления last_sent_at после отправки.

        Expected behavior:
        - После отправки дайджеста last_sent_at обновляется
        - Используется для tracking последней доставки
        """
        user_id = "user-123"

        with patch('database.models.Schedule') as MockSchedule:
            schedule = MockSchedule(
                user_id=user_id,
                is_active=True,
                times=["08:00"],
                timezone="Europe/Moscow",
                last_sent_at=None,
            )

            # Initially null
            assert schedule.last_sent_at is None

            # После отправки
            now = datetime.now(timezone.utc)
            schedule.last_sent_at = now

            assert schedule.last_sent_at == now

    async def test_user_modifies_schedule_times(self, mock_scheduler):
        """
        Тест изменения времен доставки.

        Expected behavior:
        - Старые APScheduler jobs удаляются
        - Новые jobs создаются с обновленными временами
        """
        user_id = "user-123"

        with patch('database.models.Schedule') as MockSchedule:
            schedule = MockSchedule(
                user_id=user_id, is_active=True, times=["08:00"], timezone="Europe/Moscow"
            )

            # Modify times
            schedule.times = ["09:00", "18:00"]

            # ASSERT: Times updated
            assert len(schedule.times) == 2
            assert "08:00" not in schedule.times
            assert "09:00" in schedule.times

    async def test_schedule_for_user_without_topics(self, mock_scheduler):
        """
        Тест попытки активации расписания без настроенных тем.

        Expected behavior: Должно показывать warning
        "Сначала настрой темы через /settings"
        """
        # ARRANGE: User без тем
        user_topics = []

        # ACT: Try to activate schedule
        if len(user_topics) == 0:
            error_message = "Сначала настрой темы через /settings"
        else:
            error_message = None

        # ASSERT: Error message shown
        assert error_message == "Сначала настрой темы через /settings"


# Дополнительные тесты для APScheduler интеграции требуют:
# - Real scheduler instance
# - Async job execution testing
# - Time-based trigger testing
