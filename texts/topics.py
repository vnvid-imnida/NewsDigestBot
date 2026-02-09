"""Topic-related message templates."""

# Success messages
TOPICS_SAVED_MESSAGE = (
    "✅ *Темы успешно сохранены!*\n\n"
    "*Ваши интересы:*\n"
    "{formatted_list}\n\n"
    "Используйте /digest для получения новостей!\n"
    "Изменить можно в любой момент через /settings"
)

TOPICS_LOADED_MESSAGE = (
    "📋 *Ваши текущие темы ({count}/10):*\n"
    "{topics_list}\n\n"
    "Хотите изменить темы?"
)

# Topic list display
TOPICS_LIST_HEADER = "📋 *Ваши темы ({count}/10):*"
TOPICS_LIST_EMPTY = "У вас пока нет сохраненных тем."

# Validation errors
TOPIC_TOO_SHORT_ERROR = (
    "❌ Тема слишком короткая. Минимум 2 символа.\n"
    "Попробуйте ещё раз:"
)
TOPIC_TOO_LONG_ERROR = (
    "❌ Тема слишком длинная. Максимум 100 символов.\n"
    "Попробуйте ещё раз:"
)
TOPIC_DUPLICATE_ERROR = (
    "❌ Эта тема уже добавлена.\n"
    "Введите другую тему:"
)
MAX_TOPICS_ERROR = (
    "❌ Достигнут лимит в 10 тем!\n"
    "Удалите существующие темы, чтобы добавить новые."
)

# Database errors
TOPICS_SAVE_ERROR = (
    "❌ Не удалось сохранить темы. Попробуйте позже."
)
TOPICS_LOAD_ERROR = (
    "❌ Не удалось загрузить темы. Попробуйте позже."
)

# Log messages
LOG_TOPICS_SAVED = "User {telegram_id} saved {count} topics: {topics}"
LOG_TOPICS_LOADED = "Loaded {count} topics for user {telegram_id}"
LOG_TOPICS_DELETED = "Deleted all topics for user {telegram_id}"
