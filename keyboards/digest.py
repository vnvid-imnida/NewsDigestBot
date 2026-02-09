"""Digest keyboard with inline buttons."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from texts.digest import SAVE_ARTICLE_BUTTON, SAVED_ARTICLE_BUTTON


def get_article_keyboard(
    article_external_id: str,
    is_saved: bool = False
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for a single article.

    Args:
        article_external_id: External ID of the article (MD5 hash of URL)
        is_saved: Whether article is already saved to library
    """
    if is_saved:
        button_text = SAVED_ARTICLE_BUTTON
        callback_data = f"saved:{article_external_id}"
    else:
        button_text = SAVE_ARTICLE_BUTTON
        callback_data = f"save:{article_external_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )]
        ]
    )


def get_digest_keyboard(
    articles_external_ids: list[str],
    saved_ids: set[str] | None = None
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for multiple articles (compact view).

    Args:
        articles_external_ids: List of article external IDs
        saved_ids: Set of already saved article external IDs
    """
    saved_ids = saved_ids or set()
    buttons = []

    for i, ext_id in enumerate(articles_external_ids, 1):
        is_saved = ext_id in saved_ids
        if is_saved:
            text = f"✅ {i}"
            callback_data = f"saved:{ext_id}"
        else:
            text = f"💾 {i}"
            callback_data = f"save:{ext_id}"
        buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data))

    # Group buttons in rows of 5
    rows = []
    for i in range(0, len(buttons), 5):
        rows.append(buttons[i:i + 5])

    return InlineKeyboardMarkup(inline_keyboard=rows)
