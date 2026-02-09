"""Schedule handler for /schedule command."""

import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.connection import get_session
from database.repositories.schedule import ScheduleRepository
from database.repositories.user import UserRepository
from keyboards import schedule as schedule_kb
from keyboards import main_menu
from states.schedule_state import ScheduleStates
from texts.schedule import (
    SCHEDULE_STATUS_MESSAGE,
    SCHEDULE_EMPTY_MESSAGE,
    TIME_SELECTION_MESSAGE,
    SCHEDULE_SAVED_MESSAGE,
    SCHEDULE_DISABLED_MESSAGE,
    SCHEDULE_ENABLED_MESSAGE,
    NO_TIMES_SELECTED_ERROR,
    MAX_TIMES_REACHED_ERROR,
    SCHEDULE_SAVE_ERROR,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    BACK_TO_MENU,
    EDIT_TIMES,
    TOGGLE_SCHEDULE,
    LOG_SCHEDULE_SAVED,
    LOG_SCHEDULE_TOGGLED,
)
from texts.start import SCHEDULE

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("schedule"))
@router.message(F.text == SCHEDULE)
async def cmd_schedule(message: types.Message, state: FSMContext):
    """
    Handle /schedule command - show schedule settings.
    """
    telegram_id = message.from_user.id

    # Get current schedule
    schedule = None
    try:
        async with get_session() as session:
            schedule_repo = ScheduleRepository(session)
            schedule = await schedule_repo.get_by_telegram_id(telegram_id)
    except Exception as e:
        logger.error(f"Error loading schedule for user {telegram_id}: {e}")

    if schedule is None:
        # No schedule configured
        await message.answer(
            text=SCHEDULE_EMPTY_MESSAGE,
            parse_mode="Markdown",
            reply_markup=schedule_kb.get_schedule_menu_keyboard(has_schedule=False)
        )
        return

    # Format current schedule
    status = STATUS_ACTIVE if schedule.is_active else STATUS_INACTIVE
    times = ", ".join(schedule.times) if schedule.times else "Не установлено"

    await message.answer(
        text=SCHEDULE_STATUS_MESSAGE.format(
            status=status,
            times=times,
            timezone=schedule.timezone,
        ),
        parse_mode="Markdown",
        reply_markup=schedule_kb.get_schedule_actions_keyboard(schedule.is_active)
    )


@router.message(F.text == EDIT_TIMES)
async def edit_times_handler(message: types.Message, state: FSMContext):
    """
    Start time selection flow.
    """
    telegram_id = message.from_user.id

    # Get current times if any
    selected_times = set()
    try:
        async with get_session() as session:
            schedule_repo = ScheduleRepository(session)
            schedule = await schedule_repo.get_by_telegram_id(telegram_id)
            if schedule and schedule.times:
                selected_times = set(schedule.times)
    except Exception as e:
        logger.error(f"Error loading schedule for user {telegram_id}: {e}")

    # Save to state
    await state.update_data(selected_times=list(selected_times))
    await state.set_state(ScheduleStates.selecting_times)

    selected_str = ", ".join(sorted(selected_times)) if selected_times else "ничего"

    await message.answer(
        text=TIME_SELECTION_MESSAGE.format(selected=selected_str),
        parse_mode="Markdown",
        reply_markup=schedule_kb.get_time_selection_keyboard(selected_times)
    )


@router.callback_query(F.data.startswith("time:"))
async def time_selection_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Handle time slot toggle.
    """
    time_val = callback.data.split(":", 1)[1]

    # Get current selection
    data = await state.get_data()
    selected_times = set(data.get("selected_times", []))

    # Toggle time
    if time_val in selected_times:
        selected_times.remove(time_val)
    else:
        # Check max limit
        if len(selected_times) >= 3:
            await callback.answer(MAX_TIMES_REACHED_ERROR)
            return
        selected_times.add(time_val)

    # Update state
    await state.update_data(selected_times=list(selected_times))

    selected_str = ", ".join(sorted(selected_times)) if selected_times else "ничего"

    # Update message
    await callback.message.edit_text(
        text=TIME_SELECTION_MESSAGE.format(selected=selected_str),
        parse_mode="Markdown",
        reply_markup=schedule_kb.get_time_selection_keyboard(selected_times)
    )
    await callback.answer()


@router.callback_query(F.data == "schedule:save")
async def save_schedule_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Save schedule settings.
    """
    telegram_id = callback.from_user.id

    # Get selected times
    data = await state.get_data()
    selected_times = sorted(data.get("selected_times", []))

    if not selected_times:
        await callback.answer(NO_TIMES_SELECTED_ERROR)
        return

    # Save to database
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

            # Save schedule
            schedule_repo = ScheduleRepository(session)
            await schedule_repo.create_or_update(
                user_id=db_user.id,
                times=selected_times,
                is_active=True,
            )

            logger.info(LOG_SCHEDULE_SAVED.format(
                telegram_id=telegram_id,
                times=selected_times
            ))

    except Exception as e:
        logger.error(f"Error saving schedule for user {telegram_id}: {e}")
        await callback.answer(SCHEDULE_SAVE_ERROR)
        return

    # Format times for display
    times_str = "\n".join([f"• {t}" for t in selected_times])

    await callback.message.edit_text(
        text=SCHEDULE_SAVED_MESSAGE.format(times=times_str),
        parse_mode="Markdown"
    )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "schedule:cancel")
async def cancel_schedule_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Cancel schedule editing.
    """
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "schedule:toggle")
async def toggle_schedule_callback(callback: types.CallbackQuery):
    """
    Toggle schedule on/off.
    """
    telegram_id = callback.from_user.id

    try:
        async with get_session() as session:
            # Get user
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(telegram_id)
            if not db_user:
                await callback.answer("Ошибка: пользователь не найден")
                return

            # Toggle schedule
            schedule_repo = ScheduleRepository(session)
            schedule = await schedule_repo.toggle_active(db_user.id)

            if schedule is None:
                await callback.answer("Расписание не настроено")
                return

            logger.info(LOG_SCHEDULE_TOGGLED.format(
                telegram_id=telegram_id,
                is_active=schedule.is_active
            ))

            # Send status message
            if schedule.is_active:
                await callback.message.edit_text(
                    text=SCHEDULE_ENABLED_MESSAGE,
                    parse_mode="Markdown"
                )
            else:
                await callback.message.edit_text(
                    text=SCHEDULE_DISABLED_MESSAGE,
                    parse_mode="Markdown"
                )

            await callback.answer()

    except Exception as e:
        logger.error(f"Error toggling schedule for user {telegram_id}: {e}")
        await callback.answer("Ошибка при изменении расписания")


@router.callback_query(F.data == "schedule:edit")
async def edit_schedule_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Start editing schedule times.
    """
    telegram_id = callback.from_user.id

    # Get current times
    selected_times = set()
    try:
        async with get_session() as session:
            schedule_repo = ScheduleRepository(session)
            schedule = await schedule_repo.get_by_telegram_id(telegram_id)
            if schedule and schedule.times:
                selected_times = set(schedule.times)
    except Exception as e:
        logger.error(f"Error loading schedule for user {telegram_id}: {e}")

    # Save to state
    await state.update_data(selected_times=list(selected_times))
    await state.set_state(ScheduleStates.selecting_times)

    selected_str = ", ".join(sorted(selected_times)) if selected_times else "ничего"

    await callback.message.edit_text(
        text=TIME_SELECTION_MESSAGE.format(selected=selected_str),
        parse_mode="Markdown",
        reply_markup=schedule_kb.get_time_selection_keyboard(selected_times)
    )
    await callback.answer()


@router.message(F.text == BACK_TO_MENU)
async def back_to_menu_handler(message: types.Message, state: FSMContext):
    """
    Return to main menu.
    """
    await state.clear()
    await message.answer(
        text="Главное меню",
        reply_markup=main_menu.get_main_keyboard()
    )


@router.message(F.text == TOGGLE_SCHEDULE)
async def toggle_schedule_button(message: types.Message):
    """
    Handle toggle button from reply keyboard.
    """
    telegram_id = message.from_user.id

    try:
        async with get_session() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(telegram_id)
            if not db_user:
                await message.answer("Сначала настройте расписание")
                return

            schedule_repo = ScheduleRepository(session)
            schedule = await schedule_repo.toggle_active(db_user.id)

            if schedule is None:
                await message.answer("Расписание не настроено")
                return

            logger.info(LOG_SCHEDULE_TOGGLED.format(
                telegram_id=telegram_id,
                is_active=schedule.is_active
            ))

            if schedule.is_active:
                await message.answer(
                    text=SCHEDULE_ENABLED_MESSAGE,
                    parse_mode="Markdown",
                    reply_markup=schedule_kb.get_schedule_menu_keyboard(has_schedule=True)
                )
            else:
                await message.answer(
                    text=SCHEDULE_DISABLED_MESSAGE,
                    parse_mode="Markdown",
                    reply_markup=schedule_kb.get_schedule_menu_keyboard(has_schedule=True)
                )

    except Exception as e:
        logger.error(f"Error toggling schedule for user {telegram_id}: {e}")
        await message.answer("Ошибка при изменении расписания")
