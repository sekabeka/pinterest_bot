from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

time_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text='00:00:30'
            )
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)