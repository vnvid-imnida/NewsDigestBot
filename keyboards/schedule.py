"""Schedule keyboard with time slot selection."""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from texts.schedule import (
    TOGGLE_SCHEDULE,
    EDIT_TIMES,
    BACK_TO_MENU,
    SAVE_SCHEDULE,
    CANCEL_SCHEDULE,
    AVAILABLE_TIMES,
)


def get_schedule_menu_keyboard(has_schedule: bool = False) -> ReplyKeyboardMarkup:
    """
    Main schedule menu keyboard.

    Args:
        has_schedule: Whether user has existing schedule
    """
    buttons = []

    if has_schedule:
        buttons.append([KeyboardButton(text=TOGGLE_SCHEDULE)])

    buttons.append([KeyboardButton(text=EDIT_TIMES)])
    buttons.append([KeyboardButton(text=BACK_TO_MENU)])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )


def get_time_selection_keyboard(
    selected_times: set[str] | None = None,
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for time slot selection.

    Args:
        selected_times: Set of currently selected times (HH:MM format)
    """
    selected_times = selected_times or set()
    buttons = []

    # Group times by period
    morning_times = [t for t in AVAILABLE_TIMES if t[0] < "12:00"]
    afternoon_times = [t for t in AVAILABLE_TIMES if "12:00" <= t[0] < "18:00"]
    evening_times = [t for t in AVAILABLE_TIMES if t[0] >= "18:00"]

    # Morning row
    morning_row = []
    for time_val, time_label in morning_times:
        is_selected = time_val in selected_times
        text = f"✅ {time_label}" if is_selected else time_label
        morning_row.append(InlineKeyboardButton(
            text=text,
            callback_data=f"time:{time_val}"
        ))
    if morning_row:
        buttons.append(morning_row)

    # Afternoon row
    afternoon_row = []
    for time_val, time_label in afternoon_times:
        is_selected = time_val in selected_times
        text = f"✅ {time_label}" if is_selected else time_label
        afternoon_row.append(InlineKeyboardButton(
            text=text,
            callback_data=f"time:{time_val}"
        ))
    if afternoon_row:
        buttons.append(afternoon_row)

    # Evening row
    evening_row = []
    for time_val, time_label in evening_times:
        is_selected = time_val in selected_times
        text = f"✅ {time_label}" if is_selected else time_label
        evening_row.append(InlineKeyboardButton(
            text=text,
            callback_data=f"time:{time_val}"
        ))
    if evening_row:
        buttons.append(evening_row)

    # Action buttons
    buttons.append([
        InlineKeyboardButton(text=SAVE_SCHEDULE, callback_data="schedule:save"),
        InlineKeyboardButton(text=CANCEL_SCHEDULE, callback_data="schedule:cancel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_schedule_actions_keyboard(is_active: bool) -> InlineKeyboardMarkup:
    """
    Inline keyboard for schedule actions.

    Args:
        is_active: Whether schedule is currently active
    """
    toggle_text = "⏸ Отключить" if is_active else "▶️ Включить"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=toggle_text,
                    callback_data="schedule:toggle"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=EDIT_TIMES,
                    callback_data="schedule:edit"
                ),
            ],
        ]
    )
