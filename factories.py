from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging

from aiogram.types import ParseMode
from aiohttp import web

from web.routes import routes as webapp_routes
from config.settings import settings


storage = MemoryStorage()
bot = Bot(token=settings.TELEGRAM_API_KEY, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig()
logger = logging.getLogger('ANTIHERO')
logger.setLevel(logging.INFO)


app = web.Application()
app["bot"] = bot
app.add_routes(webapp_routes)
app.router.add_static(prefix='/static', path='web/static')