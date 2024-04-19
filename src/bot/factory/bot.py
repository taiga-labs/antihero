from aiogram import Bot
from settings import config


def create_bot() -> Bot:
    return Bot(token=config.telegram_bot.TELEGRAM_BOT_TOKEN.get_secret_value(), parse_mode="HTML")
