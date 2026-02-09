"""Digest handler for /digest command."""

import logging
from aiogram import Router, types, F
from aiogram.filters import Command

from database.connection import get_session
from database.repositories.article import ArticleRepository
from database.repositories.user import UserRepository
from keyboards import digest as digest_kb
from services.digest import digest_service, DigestResult
from texts.digest import (
    NO_NEWS_MESSAGE,
    NO_TOPICS_MESSAGE,
    API_ERROR_MESSAGE,
    RATE_LIMIT_MESSAGE,
    ARTICLE_SAVED_MESSAGE,
    ARTICLE_ALREADY_SAVED_MESSAGE,
    ARTICLE_SAVE_ERROR_MESSAGE,
    LOG_DIGEST_REQUESTED,
    LOG_DIGEST_GENERATED,
    LOG_ARTICLE_SAVED,
)
from texts.start import GET_DIGEST

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("digest"))
@router.message(F.text == GET_DIGEST)
async def cmd_digest(message: types.Message):
    """
    Handle /digest command - generate and send personalized news digest.
    """
    telegram_id = message.from_user.id
    logger.info(LOG_DIGEST_REQUESTED.format(telegram_id=telegram_id))

    # Send "typing" action while fetching
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Generate digest
    result = await digest_service.generate_digest(telegram_id)

    # Handle errors
    if result.error == "no_topics":
        await message.answer(
            text=NO_TOPICS_MESSAGE,
            parse_mode="Markdown"
        )
        return

    if result.error == "rate_limit":
        await message.answer(
            text=RATE_LIMIT_MESSAGE,
            parse_mode="Markdown"
        )
        return

    if result.error in ("api_error", "database_error"):
        await message.answer(
            text=API_ERROR_MESSAGE,
            parse_mode="Markdown"
        )
        return

    # Handle no news found
    if not result.articles:
        await message.answer(
            text=NO_NEWS_MESSAGE,
            parse_mode="Markdown"
        )
        return

    # Format and send digest
    digest_text = digest_service.format_digest_message(result)

    # Get external IDs for keyboard
    article_ids = [a.external_id for a in result.articles]

    # Check which articles are already saved
    saved_ids = set()
    try:
        async with get_session() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(telegram_id)
            if db_user:
                # Import here to avoid circular imports
                from database.repositories.library import LibraryRepository
                library_repo = LibraryRepository(session)
                saved_ids = await library_repo.get_saved_external_ids(
                    db_user.id, article_ids
                )
    except Exception as e:
        logger.error(f"Error checking saved articles: {e}")

    # Create keyboard with save buttons
    keyboard = digest_kb.get_digest_keyboard(article_ids, saved_ids)

    # Store articles in cache for later saving
    # (articles are cached by external_id in news_api cache)

    await message.answer(
        text=digest_text,
        parse_mode="Markdown",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

    logger.info(LOG_DIGEST_GENERATED.format(
        count=len(result.articles),
        telegram_id=telegram_id
    ))


@router.callback_query(F.data.startswith("save:"))
async def save_article_callback(callback: types.CallbackQuery):
    """
    Handle save article button click.
    """
    external_id = callback.data.split(":", 1)[1]
    telegram_id = callback.from_user.id

    try:
        async with get_session() as session:
            # Get or create user
            user_repo = UserRepository(session)
            db_user, _ = await user_repo.get_or_create(
                telegram_id=telegram_id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                language_code=callback.from_user.language_code or "ru",
            )

            # Import here to avoid circular imports
            from database.repositories.library import LibraryRepository
            library_repo = LibraryRepository(session)

            # Check if already saved
            if await library_repo.is_saved(db_user.id, external_id):
                await callback.answer(ARTICLE_ALREADY_SAVED_MESSAGE)
                return

            # Get article from cache or create stub
            article_repo = ArticleRepository(session)
            article = await article_repo.get_by_external_id(external_id)

            if article is None:
                # Article not in DB - get from cache
                from utils.cache import articles_cache
                # Try to find in any cached search results
                # For now, create a minimal stub
                article, _ = await article_repo.create_or_update(
                    external_id=external_id,
                    title="Saved article",
                    url=f"article:{external_id}",
                )

            # Save to library
            await library_repo.save_article(db_user.id, article.id)

            logger.info(LOG_ARTICLE_SAVED.format(
                telegram_id=telegram_id,
                article_id=external_id
            ))

            await callback.answer(ARTICLE_SAVED_MESSAGE)

            # Update keyboard to show saved state
            if callback.message:
                # For now, just answer - full keyboard update would require message edit
                pass

    except Exception as e:
        logger.error(f"Error saving article {external_id} for user {telegram_id}: {e}")
        await callback.answer(ARTICLE_SAVE_ERROR_MESSAGE)


@router.callback_query(F.data.startswith("saved:"))
async def already_saved_callback(callback: types.CallbackQuery):
    """
    Handle click on already saved article button.
    """
    await callback.answer(ARTICLE_ALREADY_SAVED_MESSAGE)
