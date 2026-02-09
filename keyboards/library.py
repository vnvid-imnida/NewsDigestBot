"""Library keyboard with pagination and delete buttons."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from texts.library import (
    DELETE_BUTTON,
    CONFIRM_DELETE,
    CANCEL_DELETE,
    PREV_PAGE,
    NEXT_PAGE,
)


def get_library_keyboard(
    page: int,
    total_pages: int,
    article_ids: list[str],
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for library view with pagination.

    Args:
        page: Current page (1-indexed)
        total_pages: Total number of pages
        article_ids: List of article external IDs on current page
    """
    buttons = []

    # Delete buttons for each article
    for i, article_id in enumerate(article_ids, 1):
        buttons.append([
            InlineKeyboardButton(
                text=f"{DELETE_BUTTON} {i}",
                callback_data=f"lib_del:{article_id}"
            )
        ])

    # Pagination row
    pagination_row = []

    if page > 1:
        pagination_row.append(InlineKeyboardButton(
            text=PREV_PAGE,
            callback_data=f"lib_page:{page - 1}"
        ))

    if page < total_pages:
        pagination_row.append(InlineKeyboardButton(
            text=NEXT_PAGE,
            callback_data=f"lib_page:{page + 1}"
        ))

    if pagination_row:
        buttons.append(pagination_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_confirm_keyboard(article_id: str) -> InlineKeyboardMarkup:
    """
    Create confirmation keyboard for article deletion.

    Args:
        article_id: Article external ID
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=CONFIRM_DELETE,
                    callback_data=f"lib_confirm_del:{article_id}"
                ),
                InlineKeyboardButton(
                    text=CANCEL_DELETE,
                    callback_data="lib_cancel_del"
                ),
            ]
        ]
    )


def get_library_compact_keyboard(
    page: int,
    total_pages: int,
    articles_count: int,
) -> InlineKeyboardMarkup:
    """
    Create compact keyboard for library (no individual delete buttons).

    Args:
        page: Current page (1-indexed)
        total_pages: Total number of pages
        articles_count: Number of articles on current page
    """
    buttons = []

    # Row with delete buttons numbered
    if articles_count > 0:
        delete_row = []
        for i in range(1, articles_count + 1):
            delete_row.append(InlineKeyboardButton(
                text=f"🗑{i}",
                callback_data=f"lib_del_idx:{page}:{i}"
            ))
        # Split into rows of 5
        for i in range(0, len(delete_row), 5):
            buttons.append(delete_row[i:i + 5])

    # Pagination row
    pagination_row = []

    if page > 1:
        pagination_row.append(InlineKeyboardButton(
            text=PREV_PAGE,
            callback_data=f"lib_page:{page - 1}"
        ))

    if page < total_pages:
        pagination_row.append(InlineKeyboardButton(
            text=NEXT_PAGE,
            callback_data=f"lib_page:{page + 1}"
        ))

    if pagination_row:
        buttons.append(pagination_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
