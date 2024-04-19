from aiogram import Bot, Dispatcher

from src.bot.factory.bot import create_bot
from src.bot.factory.dispatcher import create_dispatcher

bot: Bot = create_bot()
dispatcher: Dispatcher = create_dispatcher()


