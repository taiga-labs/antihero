from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging

from aiogram.types import ParseMode

from settings import settings
from src.bot.middlewares.locale import LocalizationMiddleware

storage = MemoryStorage()
bot = Bot(token=settings.TELEGRAM_API_KEY.get_secret_value(), parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(format='%(asctime)s | %(name)s | %(message)s',
                    datefmt='%m-%d %H:%M')
logger = logging.getLogger("ANTIHERO")
logger.setLevel(logging.INFO)

i18n = LocalizationMiddleware('antihero', 'locales')
_ = i18n.lazy_gettext
