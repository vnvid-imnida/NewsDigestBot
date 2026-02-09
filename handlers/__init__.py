"""Handlers module with error handling middleware."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseMiddleware):
    """Middleware for handling errors gracefully."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error in handler: {e}", exc_info=True)

            # Try to send error message to user
            error_message = (
                "❌ Произошла ошибка при обработке запроса.\n"
                "Пожалуйста, попробуйте позже или обратитесь в поддержку."
            )

            try:
                if isinstance(event, Message):
                    await event.answer(error_message)
                elif isinstance(event, CallbackQuery):
                    await event.answer(error_message[:200])  # Callback answers have length limit
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")

            return None


__all__ = [
    "start",
    "settings",
    "digest",
    "schedule",
    "library",
    "stats",
    "ErrorHandlingMiddleware",
]
