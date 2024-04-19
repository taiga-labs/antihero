from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup as Markup


def main_menu():
    reply_markup = Markup(
        inline_keyboard=[
            [
                Button(text="Мои Герои", callback_data="heroes"),
                Button(text="Кошелёк", callback_data="wallet"),
                Button(text="ТОП", callback_data="top"),
                Button(text="Игра", callback_data="game"),
            ]
        ]
    )
    return reply_markup

