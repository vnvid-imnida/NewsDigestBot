"""Handlers for /start and /help."""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from texts.start import *
from keyboards import main_menu

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Enhanced /start command with detailed information."""
    user = message.from_user

    # TODO: Create or update user in database

    # Send main welcome message
    await message.answer(
        text=WELCOME_MESSAGE,
        parse_mode='Markdown',
        disable_web_page_preview=True,
        reply_markup=main_menu.get_main_keyboard()
    )

    # Send setup prompt
    await message.answer(
        text=ENTER_SETTINGS_MESSAGE,
        parse_mode='Markdown'
    )

    # Log
    logger.info(
        LOG_START_MESSAGE.format(
            user_id=user.id,
            username=user.username if user.username else "no_username",
            user_full_name=user.full_name
        )
    )


@router.message(Command('help'))
@router.message(F.text == HELP)
async def cmd_help(message: Message):
    """/help command with detailed information."""

    # Send help message
    await message.answer(
        text=HELP_MESSAGE,
        parse_mode='Markdown',
        disable_web_page_preview=True,
        reply_markup=main_menu.get_main_keyboard()
    )

    # Log
    logger.info(LOG_HELP_MESSAGE.format(username=message.from_user.username))
