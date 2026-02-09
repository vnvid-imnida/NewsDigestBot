from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from texts.start import *


def get_main_keyboard():
    """
    Main menu after /start
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=GET_DIGEST), KeyboardButton(text=MY_LIBRARY)],
            [KeyboardButton(text=SETTINGS), KeyboardButton(text=SCHEDULE)],
            [KeyboardButton(text=HELP), KeyboardButton(text=STATS)]
        ],
        resize_keyboard=True,
        input_field_placeholder='Choose action or type command...'
    )
    return keyboard
