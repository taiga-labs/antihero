import os
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
import logging

from config.settings import settings

if not settings.DEV:
    logging.error("Application has no file .env")
    exit(0)

storage = MemoryStorage()
bot = Bot(token=settings.TELEGRAM_API_KEY, parse_mode='Markdown')
dp = Dispatcher(bot, storage=storage)
logging.getLogger('poull_log').setLevel(logging.DEBUG)
