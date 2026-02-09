"""Library message templates."""

# Library header
LIBRARY_HEADER = (
    "💾 *Ваша библиотека*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
)

LIBRARY_COUNT_INFO = "📚 Сохранено статей: {count}\n\n"

# Article item format
LIBRARY_ITEM_FORMAT = (
    "{num}. *{title}*\n"
    "   📍 {source} • {saved_date}\n"
    "   [Читать]({url})\n"
)

# Pagination info
PAGINATION_INFO = "\n📄 Страница {page} из {total_pages}"

# Empty library
EMPTY_LIBRARY_MESSAGE = (
    "📭 *Библиотека пуста*\n\n"
    "Здесь будут храниться сохраненные статьи.\n\n"
    "Чтобы сохранить статью:\n"
    "1. Запросите дайджест: /digest\n"
    "2. Нажмите 💾 под интересной статьей"
)

# Delete confirmation
DELETE_CONFIRM_MESSAGE = (
    "🗑 *Удалить статью?*\n\n"
    "*{title}*\n\n"
    "Это действие нельзя отменить."
)

# Success messages
ARTICLE_DELETED_MESSAGE = "✅ Статья удалена из библиотеки"

# Error messages
LIBRARY_LOAD_ERROR = "❌ Не удалось загрузить библиотеку. Попробуйте позже."
DELETE_ERROR_MESSAGE = "❌ Не удалось удалить статью"

# Button texts
DELETE_BUTTON = "🗑 Удалить"
CONFIRM_DELETE = "✅ Да, удалить"
CANCEL_DELETE = "❌ Отмена"
PREV_PAGE = "◀️ Назад"
NEXT_PAGE = "Вперед ▶️"

# Log messages
LOG_LIBRARY_VIEWED = "User {telegram_id} viewed library (page {page})"
LOG_ARTICLE_DELETED = "User {telegram_id} deleted article {article_id} from library"
