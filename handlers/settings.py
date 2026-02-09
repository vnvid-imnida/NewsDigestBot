"""Settings handler for topic management."""

import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from database.connection import get_session
from database.repositories.topic import TopicRepository
from database.repositories.user import UserRepository
from texts.start import SETTINGS
from texts.settings import (
    SETTINGS_MESSAGE,
    ASK_CURRENT_STEP_TOPIC_MESSAGE,
    MAXIMUM_REACHED_MESSAGE,
    NEXT_TOPIC_MESSAGE,
    PROCESS_TOPIC_MESSAGE,
    CANCEL_SAVE_MESSAGE,
    ENTER_TOPIC,
    STOP_ENTERING,
    FINISH_SAVE,
    CLEAR_RESTART,
    SAVE_TOPICS,
    EDIT_TOPICS,
    CANCEL,
    MAX_TOPICS_REACHED_ERROR,
    NO_TOPICS_TO_SAVE_ERROR,
    PREVIEW_MESSAGE,
    LOG_USER_TOPICS,
)
from texts.topics import (
    TOPICS_SAVED_MESSAGE,
    TOPICS_LOADED_MESSAGE,
    TOPIC_TOO_SHORT_ERROR,
    TOPIC_TOO_LONG_ERROR,
    TOPIC_DUPLICATE_ERROR,
    MAX_TOPICS_ERROR,
    TOPICS_SAVE_ERROR,
    TOPICS_LOAD_ERROR,
    LOG_TOPICS_SAVED,
    LOG_TOPICS_LOADED,
)
from keyboards import main_menu, settings
from keyboards.settings import KEEP_TOPICS
from utils.format_output import format_topics_list
from states.waiting_for_topic_state import SettingsStates

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("settings"))
@router.message(F.text == SETTINGS)
async def cmd_settings(message: types.Message, state: FSMContext):
    """
    Start of step-by-step topic entry.
    Loads existing topics from database if user has any.
    """
    telegram_id = message.from_user.id

    # Load existing topics from database
    existing_topics = []
    try:
        async with get_session() as session:
            topic_repo = TopicRepository(session)
            db_topics = await topic_repo.list_by_telegram_id(telegram_id)
            existing_topics = [t.name for t in db_topics]
            logger.info(LOG_TOPICS_LOADED.format(
                count=len(existing_topics),
                telegram_id=telegram_id
            ))
    except Exception as e:
        logger.error(f"Error loading topics for user {telegram_id}: {e}")

    # If user has existing topics, show them and offer to edit
    if existing_topics:
        topics_list = format_topics_list(existing_topics)
        await message.answer(
            text=TOPICS_LOADED_MESSAGE.format(
                count=len(existing_topics),
                topics_list=topics_list
            ),
            parse_mode="Markdown",
            reply_markup=settings.get_edit_existing_keyboard()
        )
        # Store existing topics in state for potential editing
        await state.update_data(
            user_topics=existing_topics,
            current_step=len(existing_topics) + 1,
            max_topics=10,
            has_existing_topics=True
        )
        return

    # No existing topics - start fresh
    await state.update_data(
        user_topics=[],
        current_step=1,
        max_topics=10,
        has_existing_topics=False
    )

    await message.answer(
        text=SETTINGS_MESSAGE,
        parse_mode="Markdown",
        reply_markup=settings.get_settings_keyboard()
    )


@router.message(F.text.startswith(ENTER_TOPIC))
async def start_topic_entry(message: types.Message, state: FSMContext):
    """
    Start topic entry.
    """
    user_data = await state.get_data()
    current_step = user_data.get("current_step", 1)
    user_topics = user_data.get("user_topics", [])

    # Check limits
    if len(user_topics) >= 10:
        await message.answer(
            text=MAX_TOPICS_ERROR,
            reply_markup=settings.get_max_topics_keyboard()
        )
        return

    await message.answer(
        text=ASK_CURRENT_STEP_TOPIC_MESSAGE.format(
            current_step=current_step
        ),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(SettingsStates.waiting_for_topic)


@router.message(SettingsStates.waiting_for_topic)
async def process_topic_input(message: types.Message, state: FSMContext):
    """
    Processing entered topic with validation.
    """
    topic = message.text.strip()

    # Validation: minimum length
    if len(topic) < 2:
        await message.answer(
            text=TOPIC_TOO_SHORT_ERROR,
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Validation: maximum length
    if len(topic) > 100:
        await message.answer(
            text=TOPIC_TOO_LONG_ERROR,
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Get current data
    user_data = await state.get_data()
    user_topics = user_data.get("user_topics", [])
    current_step = user_data.get("current_step", 1)

    # Validation: unique per user (case-insensitive)
    normalized_topic = topic.lower()
    if any(t.lower() == normalized_topic for t in user_topics):
        await message.answer(
            text=TOPIC_DUPLICATE_ERROR,
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Add topic
    user_topics.append(topic)
    current_step += 1

    # Update state
    await state.update_data(
        user_topics=user_topics,
        current_step=current_step
    )

    # Reply
    topics_list = format_topics_list(user_topics)
    topics_count = len(user_topics)

    # Choose keyboard based on topic count
    if topics_count >= 10:
        keyboard = settings.get_max_topics_keyboard()
        status_text = MAXIMUM_REACHED_MESSAGE
    else:
        keyboard = settings.get_settings_keyboard(topics_count, current_step)
        status_text = NEXT_TOPIC_MESSAGE

    await message.answer(
        text=PROCESS_TOPIC_MESSAGE.format(
            topics_count=topics_count,
            topic=topic,
            topics_list=topics_list,
            status_text=status_text
        ),
        parse_mode="Markdown",
        reply_markup=keyboard
    )

    await state.set_state(None)


@router.message(F.text == STOP_ENTERING)
async def stop_entering(message: types.Message, state: FSMContext):
    """
    Stop topics entry.
    """
    await show_final_preview(message, state)


@router.message(F.text == FINISH_SAVE)
async def finish_and_save(message: types.Message, state: FSMContext):
    """
    Finish and save topics.
    """
    await show_final_preview(message, state)


@router.message(F.text == CLEAR_RESTART)
async def clear_and_restart(message: types.Message, state: FSMContext):
    """
    Clear topics and restart.
    """
    await state.clear()
    await cmd_settings(message, state)


async def show_final_preview(message: types.Message, state: FSMContext):
    """
    Show final preview before saving.
    """
    user_data = await state.get_data()
    user_topics = user_data.get("user_topics", [])

    if not user_topics:
        await message.answer(
            text=NO_TOPICS_TO_SAVE_ERROR,
            reply_markup=main_menu.get_main_keyboard()
        )
        await state.clear()
        return

    topics_list = format_topics_list(user_topics)

    await message.answer(
        text=PREVIEW_MESSAGE.format(
            topics_number=len(user_topics),
            topics_list=topics_list
        ),
        parse_mode="Markdown",
        reply_markup=settings.get_confirm_keyboard()
    )


@router.message(F.text == SAVE_TOPICS)
async def save_topics_final(message: types.Message, state: FSMContext):
    """
    Final topics saving to database.
    """
    user_data = await state.get_data()
    user_topics = user_data.get("user_topics", [])
    telegram_id = message.from_user.id

    if not user_topics:
        await message.answer(
            text=NO_TOPICS_TO_SAVE_ERROR,
            reply_markup=main_menu.get_main_keyboard()
        )
        await state.clear()
        return

    # Save to database
    try:
        async with get_session() as session:
            # Get or create user first
            user_repo = UserRepository(session)
            db_user, _ = await user_repo.get_or_create(
                telegram_id=telegram_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                language_code=message.from_user.language_code or "ru",
            )

            # Replace all topics
            topic_repo = TopicRepository(session)
            await topic_repo.replace_all(db_user.id, user_topics)

            logger.info(LOG_TOPICS_SAVED.format(
                telegram_id=telegram_id,
                count=len(user_topics),
                topics=user_topics
            ))

    except Exception as e:
        logger.error(f"Error saving topics for user {telegram_id}: {e}")
        await message.answer(
            text=TOPICS_SAVE_ERROR,
            reply_markup=main_menu.get_main_keyboard()
        )
        await state.clear()
        return

    # Format for display
    formatted_list = "\n".join([f"• {t}" for t in user_topics])

    await message.answer(
        text=TOPICS_SAVED_MESSAGE.format(
            formatted_list=formatted_list
        ),
        parse_mode="Markdown",
        reply_markup=main_menu.get_main_keyboard()
    )

    await state.clear()


@router.message(F.text == EDIT_TOPICS)
async def edit_topics(message: types.Message, state: FSMContext):
    """
    Edit topics - restart the flow.
    """
    # Clear existing topics from state and restart
    await state.update_data(
        user_topics=[],
        current_step=1,
        has_existing_topics=False
    )
    await message.answer(
        text=SETTINGS_MESSAGE,
        parse_mode="Markdown",
        reply_markup=settings.get_settings_keyboard()
    )


@router.message(F.text == CANCEL)
async def cancel_save(message: types.Message, state: FSMContext):
    """
    Cancel saving.
    """
    await message.answer(
        text=CANCEL_SAVE_MESSAGE,
        reply_markup=main_menu.get_main_keyboard()
    )
    await state.clear()


@router.message(F.text == KEEP_TOPICS)
async def keep_current_topics(message: types.Message, state: FSMContext):
    """
    Keep current topics without changes.
    """
    await message.answer(
        text="Темы сохранены без изменений.",
        reply_markup=main_menu.get_main_keyboard()
    )
    await state.clear()
