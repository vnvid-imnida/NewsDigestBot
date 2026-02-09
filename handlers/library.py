"""Library handler for /library command."""

import logging
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command

from database.connection import get_session
from database.repositories.library import LibraryRepository
from database.repositories.user import UserRepository
from keyboards import library as library_kb
from keyboards import main_menu
from texts.library import (
    LIBRARY_HEADER,
    LIBRARY_COUNT_INFO,
    LIBRARY_ITEM_FORMAT,
    PAGINATION_INFO,
    EMPTY_LIBRARY_MESSAGE,
    ARTICLE_DELETED_MESSAGE,
    LIBRARY_LOAD_ERROR,
    DELETE_ERROR_MESSAGE,
    LOG_LIBRARY_VIEWED,
    LOG_ARTICLE_DELETED,
)
from texts.start import MY_LIBRARY

logger = logging.getLogger(__name__)
router = Router()

ITEMS_PER_PAGE = 5


def format_saved_date(dt: datetime) -> str:
    """Format datetime as saved date string."""
    return dt.strftime("%d.%m.%Y")


@router.message(Command("library"))
@router.message(F.text == MY_LIBRARY)
async def cmd_library(message: types.Message):
    """
    Handle /library command - show saved articles.
    """
    telegram_id = message.from_user.id
    await show_library_page(message, telegram_id, page=1)


async def show_library_page(
    message_or_callback: types.Message | types.CallbackQuery,
    telegram_id: int,
    page: int,
    edit: bool = False,
):
    """
    Show library page.

    Args:
        message_or_callback: Message or callback query
        telegram_id: User's Telegram ID
        page: Page number (1-indexed)
        edit: Whether to edit existing message
    """
    try:
        async with get_session() as session:
            # Get user
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(telegram_id)

            if not db_user:
                text = EMPTY_LIBRARY_MESSAGE
                if isinstance(message_or_callback, types.Message):
                    await message_or_callback.answer(text, parse_mode="Markdown")
                else:
                    await message_or_callback.message.edit_text(text, parse_mode="Markdown")
                return

            # Get library
            library_repo = LibraryRepository(session)
            total_count = await library_repo.count_by_user(db_user.id)

            if total_count == 0:
                text = EMPTY_LIBRARY_MESSAGE
                if isinstance(message_or_callback, types.Message):
                    await message_or_callback.answer(text, parse_mode="Markdown")
                else:
                    await message_or_callback.message.edit_text(text, parse_mode="Markdown")
                return

            # Calculate pagination
            total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            page = max(1, min(page, total_pages))
            offset = (page - 1) * ITEMS_PER_PAGE

            # Get articles for page
            items = await library_repo.list_by_user(
                db_user.id,
                limit=ITEMS_PER_PAGE,
                offset=offset,
            )

            # Format message
            parts = [LIBRARY_HEADER]
            parts.append(LIBRARY_COUNT_INFO.format(count=total_count))

            article_ids = []
            for i, (saved_article, article) in enumerate(items, 1):
                num = offset + i
                title = _escape_markdown(article.title[:80])
                if len(article.title) > 80:
                    title += "..."
                source = article.source_name or "Источник"
                saved_date = format_saved_date(saved_article.saved_at)

                parts.append(LIBRARY_ITEM_FORMAT.format(
                    num=num,
                    title=title,
                    source=source,
                    saved_date=saved_date,
                    url=article.url,
                ))
                article_ids.append(article.external_id)

            if total_pages > 1:
                parts.append(PAGINATION_INFO.format(
                    page=page,
                    total_pages=total_pages,
                ))

            text = "".join(parts)

            # Create keyboard
            keyboard = library_kb.get_library_compact_keyboard(
                page=page,
                total_pages=total_pages,
                articles_count=len(items),
            )

            # Send or edit message
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.answer(
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
            else:
                await message_or_callback.message.edit_text(
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )

            logger.info(LOG_LIBRARY_VIEWED.format(
                telegram_id=telegram_id,
                page=page,
            ))

    except Exception as e:
        logger.error(f"Error loading library for user {telegram_id}: {e}")
        text = LIBRARY_LOAD_ERROR
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer(text, parse_mode="Markdown")
        else:
            await message_or_callback.answer(text)


def _escape_markdown(text: str) -> str:
    """Escape special Markdown characters."""
    special_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


@router.callback_query(F.data.startswith("lib_page:"))
async def library_page_callback(callback: types.CallbackQuery):
    """
    Handle library pagination.
    """
    page = int(callback.data.split(":", 1)[1])
    telegram_id = callback.from_user.id

    await show_library_page(callback, telegram_id, page, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("lib_del_idx:"))
async def delete_by_index_callback(callback: types.CallbackQuery):
    """
    Handle delete by index (from compact keyboard).
    """
    parts = callback.data.split(":")
    page = int(parts[1])
    idx = int(parts[2])  # 1-indexed
    telegram_id = callback.from_user.id

    try:
        async with get_session() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(telegram_id)

            if not db_user:
                await callback.answer("Ошибка: пользователь не найден")
                return

            library_repo = LibraryRepository(session)

            # Get the article at this index
            offset = (page - 1) * ITEMS_PER_PAGE + (idx - 1)
            items = await library_repo.list_by_user(db_user.id, limit=1, offset=offset)

            if not items:
                await callback.answer("Статья не найдена")
                return

            saved_article, article = items[0]

            # Delete from library
            await library_repo.delete_saved(db_user.id, article.id)

            logger.info(LOG_ARTICLE_DELETED.format(
                telegram_id=telegram_id,
                article_id=article.external_id,
            ))

            await callback.answer(ARTICLE_DELETED_MESSAGE)

        # Refresh page
        await show_library_page(callback, telegram_id, page, edit=True)

    except Exception as e:
        logger.error(f"Error deleting article for user {telegram_id}: {e}")
        await callback.answer(DELETE_ERROR_MESSAGE)


@router.callback_query(F.data.startswith("lib_del:"))
async def delete_article_callback(callback: types.CallbackQuery):
    """
    Handle delete article by external_id.
    """
    external_id = callback.data.split(":", 1)[1]
    telegram_id = callback.from_user.id

    try:
        async with get_session() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(telegram_id)

            if not db_user:
                await callback.answer("Ошибка: пользователь не найден")
                return

            # Get article by external_id
            from database.repositories.article import ArticleRepository
            article_repo = ArticleRepository(session)
            article = await article_repo.get_by_external_id(external_id)

            if not article:
                await callback.answer("Статья не найдена")
                return

            library_repo = LibraryRepository(session)
            deleted = await library_repo.delete_saved(db_user.id, article.id)

            if deleted:
                logger.info(LOG_ARTICLE_DELETED.format(
                    telegram_id=telegram_id,
                    article_id=external_id,
                ))
                await callback.answer(ARTICLE_DELETED_MESSAGE)
            else:
                await callback.answer("Статья не найдена в библиотеке")

        # Refresh library
        await show_library_page(callback, telegram_id, page=1, edit=True)

    except Exception as e:
        logger.error(f"Error deleting article {external_id} for user {telegram_id}: {e}")
        await callback.answer(DELETE_ERROR_MESSAGE)


@router.callback_query(F.data == "lib_cancel_del")
async def cancel_delete_callback(callback: types.CallbackQuery):
    """
    Cancel deletion.
    """
    telegram_id = callback.from_user.id
    await show_library_page(callback, telegram_id, page=1, edit=True)
    await callback.answer()
