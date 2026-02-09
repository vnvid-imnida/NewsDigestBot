# Руководство по разработке News Digest Bot

Спасибо за интерес к проекту! Этот документ описывает правила работы над News Digest Bot.

---

## Содержание

- [Настройка окружения](#настройка-окружения)
- [Структура проекта](#структура-проекта)
- [Стиль кода](#стиль-кода)
- [Тестирование](#тестирование)
- [Git Workflow](#git-workflow)
- [Процесс Pull Request](#процесс-pull-request)
- [Миграции базы данных](#миграции-базы-данных)

---

## Настройка окружения

### Требования

- Python 3.11+
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Локальное окружение

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd News
   ```

2. Создайте виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # или .venv\Scripts\activate  # Windows
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Настройте переменные окружения:
   ```bash
   cp .env.example .env
   # Отредактируйте .env, добавьте BOT_TOKEN и GNEWS_API_KEY
   ```

5. Запустите PostgreSQL:
   ```bash
   docker-compose up -d db
   ```

6. Выполните миграции:
   ```bash
   alembic upgrade head
   ```

7. Запустите бота локально:
   ```bash
   python main.py
   ```

---

## Структура проекта

```
News/
├── main.py              # Точка входа
├── config/              # Конфигурация и настройки
├── database/            # Модели БД, репозитории
├── handlers/            # Обработчики команд Telegram
├── services/            # Бизнес-логика
├── keyboards/           # Telegram клавиатуры
├── states/              # FSM состояния
├── utils/               # Вспомогательные утилиты
├── alembic/             # Миграции базы данных
├── tests/               # Тесты
└── docs/                # Документация
```

---

## Стиль кода

### Python

Следуем **PEP 8** с дополнительными правилами:

- **Длина строки**: 120 символов
- **Импорты**: группируем по категориям (stdlib, 3rd-party, local)
- **Type hints**: обязательны для функций и методов
- **Docstrings**: Google style для классов и публичных функций

**Форматирование**:
```bash
# Автоформатирование с black
black .

# Сортировка импортов
isort .

# Проверка стиля
ruff check .
```

### SQL/Alembic

- **Именование**: snake_case для таблиц и колонок
- **Миграции**: описательные имена, например `add_user_email_column`
- **Индексы**: всегда указывать имя, например `idx_users_telegram_id`

---

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Только unit тесты
pytest tests/unit

# Только integration тесты
pytest tests/integration

# С покрытием
pytest --cov=. --cov-report=html
```

### Написание тестов

- **Unit тесты**: тестируют изолированную логику (models, services)
- **Integration тесты**: тестируют полные пользовательские сценарии
- **Fixtures**: используем pytest fixtures для setup/teardown
- **Mocks**: используем `pytest-asyncio` для async кода

**Пример**:
```python
import pytest
from database.models import User

@pytest.mark.asyncio
async def test_user_creation():
    user = User(telegram_id=123456, username="testuser")
    assert user.telegram_id == 123456
    assert user.language_code == "ru"  # default
```

---

## Git Workflow

### Стратегия ветвления

- `main` - production-ready код
- `feature/<название-фичи>` - новые функции
- `bugfix/<название-бага>` - исправления багов
- `hotfix/<issue>` - срочные исправления production

### Сообщения коммитов

Используем **Conventional Commits**:

```
<type>(<scope>): <краткое описание>

<подробное описание (опционально)>

<footer (опционально)>
```

**Типы**:
- `feat`: новая функциональность
- `fix`: исправление бага
- `docs`: изменения документации
- `style`: форматирование, без изменений логики
- `refactor`: рефакторинг кода
- `test`: добавление/изменение тестов
- `chore`: обновление зависимостей, конфигурации

**Пример**:
```
feat(digest): добавлена поддержка запланированной доставки дайджестов

- Добавлена модель Schedule
- Интеграция APScheduler
- Добавлен обработчик команды /schedule

Closes #42
```

---

## Процесс Pull Request

### Чеклист перед созданием PR

- [ ] Код соответствует стилю (black, isort, ruff проходят)
- [ ] Все тесты проходят (`pytest`)
- [ ] Добавлены тесты для новой функциональности
- [ ] Обновлена документация (README, docstrings)
- [ ] Нет захардкоженных credentials или секретов
- [ ] Включены файлы миграций (если изменена схема БД)
- [ ] Сообщения коммитов следуют Conventional Commits

### Шаблон PR

```markdown
## Описание
Краткое описание изменений

## Тип изменений
- [ ] Исправление бага
- [ ] Новая функциональность
- [ ] Breaking change
- [ ] Обновление документации

## Тестирование
Как протестировать изменения

## Скриншоты (если применимо)
Добавьте скриншоты для изменений UI

## Чеклист
- [ ] Тесты проходят
- [ ] Код соответствует стилю
- [ ] Документация обновлена
```

### Процесс review

1. Создайте PR из feature ветки в `main`
2. Запросите review у члена команды
3. Учтите комментарии reviewer
4. Merge со стратегией **squash and merge**

---

## Миграции базы данных

### Создание миграции

```bash
# Автогенерация миграции из изменений моделей
alembic revision --autogenerate -m "описательное_сообщение"

# Ручная миграция
alembic revision -m "описательное_сообщение"
```

### Применение миграций

```bash
# Обновление до последней версии
alembic upgrade head

# Обновление до конкретной версии
alembic upgrade <revision>

# Откат
alembic downgrade -1
```

### Best Practices для миграций

- **Всегда проверяйте** автогенерированные миграции
- **Тестируйте миграции** в обе стороны (upgrade и downgrade)
- **Миграции данных**: используйте отдельную миграцию для изменений данных
- **Деструктивные изменения**: добавьте warning комментарии, требуйте manual review

---

## Вопросы?

Если у вас есть вопросы:
1. Проверьте [README.md](../README.md)
2. Ознакомьтесь с [quickstart.md](../specs/003-course-documentation/quickstart.md)
3. Откройте issue в GitHub

---

**Последнее обновление**: 2026-02-05
