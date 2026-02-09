<h1>Отчёт по курсовому проекту</h1>

<h2>Участники проекта</h2>
<ol>
  <li>Сафина Диана Айратовна, гр. 5130904/30102</li>
  <li>Елич Майя, гр. 5130904/30102</li>
</ol>

<h2>Тема проекта</h2>
<p>News Digest Bot – Телеграм-бот для агрегации новостей по выбранным пользователем темам с ежедневной рассылкой дайджеста</p>

<h2>Технологический стек</h2>
<ul>
  <li>UI - Telegram (UI через бота), библиотека aiogram 3.x</li>
  <li>Язык для написания серверной части – Python 3.11+</li>
  <li>База данных – PostgreSQL</li>
  <li>Внешняя зависимость – GNews API</li>
  <li>Прочие технологии – sqlalchemy, pydantic и другие</li>
</ul>

<h2>Этапы разработки</h2>
<h3>Определение проблемы</h3>
<p>Пользователи сталкиваются с информационной перегрузкой и необходимостью постоянно мониторить десятки источников новостей вручную. Отсутствие персонализированного агрегатора приводит к потере времени на поиск релевантного контента, риску пропустить важные события и получению разрозненной, нерелевантной информации.</p>

<h3>Выработка требований</h3>
<h4>Пользовательские сценарии (User Stories)</h4>
<h5>User Story 1 – Получение персонализированного дайджеста</h5>
<blockquote>Как подписчик, я хочу получать ежедневный дайджест новостей по моим темам в удобное для меня время, чтобы быть в курсе событий без информационной перегрузки.</blockquote>
<h5>User Story 2 – Автоматическая доставка дайджеста</h5>
<blockquote>Как подписчик, я хочу получать ежедневный дайджест новостей по моим темам в удобное для меня время, чтобы быть в курсе событий без информационной перегрузки.</blockquote>
<h5>User Story 3 – Управление подписками и настройками</h5>
<blockquote>Как активный пользователь, я хочу легко добавлять новые темы, удалять неактуальные и менять время рассылки, чтобы гибко настраивать сервис под свои потребности.</blockquote>

<h4>Оценка числа пользователей и периода хранения данных</h4>
<ul>
  <li><strong>Число пользователей в сутки:</strong> 10 000 пользователей (высокоуровневая оценка, соответствует рекомендации)</li>
  <li><strong>Период хранения информации:</strong> > 5 лет (сохранение истории подписок, настроек, логов отправки для анализа и отладки)</li>
</ul>

<h3>Разработĸа архитеĸтуры и детальное проеĸтирование</h3>
<h4>Хараĸтер нагрузĸи на сервис</h4>
<ul>
  <li>Соотношение R/W: 80/20 (40 000 read/day, 10 000 write/day)</li>
  <li>Объёмы трафика: пиковый RPS: 4.2 запроса/сек; суточный трафик: 50 000 сообщений; трафик к внешним API: ~1 000 запросов/день</li>
  <li>Объём дисковой системы: чистые данные за 5 лет: 120 GB; выделенный объём: 200 GB; при 10× росте: 2 TB</li>
</ul>

<h4>C4 Context diagram</h4>
<img width="514" height="857" alt="c4_context" src="https://github.com/user-attachments/assets/34820c5a-2e3d-480e-b760-f476e0aeb574" />

<h4>C4 Container diagram</h4>
<img width="953" height="1160" alt="c4_container" src="https://github.com/user-attachments/assets/e4bd85f1-f8be-48b5-8d8c-38e49215483f" />

<h4>Контракты API</h4>
<p><strong>Telegram Bot API</strong></p>
<pre>
/start                 - Регистрация
/settings [topics...]  - Настройка тем  
/digest                - Получение дайджеста
/schedule [times...]   - Настройка расписания
/save [article_id]     - Сохранение статьи
/library               - Просмотр библиотеки
</pre>

<h4>Нефункциональные требования</h4>
<ul>
  <li><strong>Производительность:</strong> Отклик ≤500мс (p95)</li>
  <li><strong>Доступность:</strong> 99.5% SLA</li>
  <li><strong>Масштабируемость:</strong> До 100к пользователей/день</li>
  <li><strong>Хранение:</strong> 5+ лет, 200GB диска</li>
  <li><strong>Безопасность:</strong> Валидация вводов, логирование</li>
</ul>

<h4>Схема базы данных</h4>
<img width="844" height="781" alt="schema" src="https://github.com/user-attachments/assets/c29ef1d8-1e60-4929-a48f-9908186d5bbf" />

<h4>Схема масштабирования сервиса при росте нагрузĸи в 10 раз</h4>

<h3>Кодирование и отладка</h3>
<p>Каждый участник внёс коммиты в репозиторий. Использовались ветки для фич, документации и код-ревью.</p>

<h3>Unit тестирование</h3>
<h4>test_article_model.py</h4>
<p>Unit tests для моделей Article и SavedArticle.</p>
<p>Тестируются:</p>
<ul>
  <li>Article model: создание, валидация, unique external_id</li>
  <li>SavedArticle model: связи user-article, unique constraint</li>
</ul>

<h4>test_models.py</h4>
<p>Unit tests для SQLAlchemy моделей базы данных.</p>
<p>Тестируются:</p>
<ul>
  <li>User model: создание, валидация, default values</li>
  <li>Topic model: unique constraint (user_id, name)</li>
  <li>Schedule model: валидация JSON times field</li>
</ul>

<h4>test_news_api.py</h4>
<p>Unit tests для NewsApiService.</p>
<p>Тестируются:</p>
<ul>
  <li>ArticleDTO.from_api_response: парсинг GNews API response</li>
  <li>NewsApiService.search: поиск статей по теме</li>
  <li>NewsApiService.search_multiple: поиск по нескольким темам</li>
  <li>NewsApiService.get_top_headlines: получение топ новостей</li>
  <li>Error handling: rate limits, API errors, network errors</li>
</ul>

<h3>Интеграционное тестирование</h3>
<h4>test_digest_flow.py</h4>
<p>Integration тест для полного сценария получения персонализированного дайджеста.</p>

<p>Покрывает User Story 1: "Получение персонализированного дайджеста новостей"</p>

<p>Сценарий:</p>
<ol>
<li>Пользователь регистрируется через /start</li>
<li>Настраивает темы интересов через /settings</li>
<li>Получает дайджест новостей через /digest</li>
<li>Сохраняет интересную статью</li>
<li>Просматривает библиотеку через /library</li>
</ol>

<p>NOTE: Для реальных integration тестов требуется:</p>
<ul>
<li>Тестовая БД (testcontainers или отдельная test database)</li>
<li>Mock Telegram Bot API</li>
<li>Mock GNews API (или test fixtures)</li>
</ul>

<p>Для полноценной интеграции с БД рекомендуется использовать:</p>
<pre>
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

@pytest_asyncio.fixture(scope="session")
async def test_db():
    with PostgresContainer("postgres:15") as postgres:
        db_url = postgres.get_connection_url()
        # Setup database schema
        yield db_url
</pre>

<h4>test_schedule_flow.py</h4>
<p>Integration тест для автоматической доставки дайджеста по расписанию.</p>

<p>Покрывает User Story 2: "Автоматическая доставка дайджеста"</p>

<p>Сценарий:</p>
<ol>
<li>Пользователь настраивает расписание через /schedule</li>
<li>Указывает время доставки (например, 08:00 и 18:00)</li>
<li>APScheduler автоматически отправляет дайджест в указанное время</li>
<li>Пользователь может изменить или отключить расписание</li>
</ol>

<p>Acceptance Criteria (из spec.md):</p>
<ul>
<li>Пользователь может установить расписание (1-3 времени в день)</li>
<li>Бот автоматически отправляет дайджест в указанное время</li>
<li>Timezonе учитывается (Europe/Moscow по умолчанию)</li>
<li>Пользователь может деактивировать расписание</li>
</ul>

<h3>Сборка</h3>
<p>Все команды выполняются через Docker Compose. Для работы требуется только Docker и Docker Compose.</p>

<h4>Основные команды:</h4>

<pre>
# Запуск всех тестов (47 тестов)
docker-compose run --rm newsbot pytest -v

# Запуск только unit-тестов (31 тест)
docker-compose run --rm newsbot pytest tests/unit -v

# Запуск только интеграционных тестов (16 тестов)
docker-compose run --rm newsbot pytest tests/integration -v

# Запуск тестов с отчетом о покрытии кода
docker-compose run --rm newsbot pytest --cov=. --cov-report=html

# Сборка и запуск приложения
docker-compose up --build
</pre>

<h4>Альтернативно через Makefile:</h4>
<pre>
test:
	docker-compose run --rm newsbot pytest -v

test-unit:
	docker-compose run --rm newsbot pytest tests/unit -v

test-integration:
	docker-compose run --rm newsbot pytest tests/integration -v

coverage:
	docker-compose run --rm newsbot pytest --cov=. --cov-report=html

up:
	docker-compose up --build
</pre>

<h4>Остановка приложения:</h4>
<pre>
# Остановить приложение
docker-compose down
# Остановить и удалить volumes
docker-compose down -v
</pre>

<p><strong>Примечание:</strong> Все зависимости, включая тестовое окружение, уже настроены в Docker-контейнерах.</p>

<h2>Заключение</h2>
<p>Проект реализует функциональность персонализированного новостного дайджеста в Telegram. Все этапы разработки пройдены, код протестирован, проект готов к дальнейшему использованию.</p>
