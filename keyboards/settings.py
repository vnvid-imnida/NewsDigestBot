from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from texts.settings import *

# Button text for existing topics menu
KEEP_TOPICS = "✅ Оставить текущие"
ADD_MORE_TOPICS = "➕ Добавить ещё"


def get_settings_keyboard(current_count: int = 0, next_step: int = 1):
    """
    A multipurpose keyboards for settings

    Args:
        current_count: Topics already added (0-10)
        next_step: Next topic number (1-10)
    """
    buttons = []

    # 1. Enter topic button if possible
    if current_count < 10:
        buttons.append([KeyboardButton(text=f"{ENTER_TOPIC} {next_step}")])

    # 2. Control buttons if there is at least 1 topic
    if current_count > 0:
        buttons.append([KeyboardButton(text=FINISH_SAVE)])
        buttons.append([KeyboardButton(text=CLEAR_RESTART)])
    else:
        # If no topics yet, only stop entering option is available
        buttons.append([KeyboardButton(text=STOP_ENTERING)])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )


def get_max_topics_keyboard():
    """
    A keyboard when a limit of 10 topics is reached
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=FINISH_SAVE)],
            [KeyboardButton(text=CLEAR_RESTART)]
        ],
        resize_keyboard=True
    )


def get_confirm_keyboard():
    """
    A keyboard to confirm saving
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SAVE_TOPICS)],
            [KeyboardButton(text=EDIT_TOPICS)],
            [KeyboardButton(text=CANCEL)]
        ],
        resize_keyboard=True
    )


def get_edit_existing_keyboard():
    """
    A keyboard shown when user has existing topics.
    Offers to keep current topics, add more, or edit (replace all).
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=KEEP_TOPICS)],
            [KeyboardButton(text=EDIT_TOPICS)],
            [KeyboardButton(text=CLEAR_RESTART)]
        ],
        resize_keyboard=True
    )