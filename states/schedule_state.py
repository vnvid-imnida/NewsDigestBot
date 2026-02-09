"""FSM states for schedule configuration."""

from aiogram.fsm.state import State, StatesGroup


class ScheduleStates(StatesGroup):
    """States for schedule configuration flow."""

    # Waiting for user to select time slots
    selecting_times = State()

    # Waiting for timezone selection
    selecting_timezone = State()

    # Confirming schedule settings
    confirming = State()
