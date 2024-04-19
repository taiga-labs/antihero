from src.bot import dispatcher, bot
from settings import config
from src.bot.runners import run_polling, run_webhook

# setup_logger()
if config.telegram_bot.USE_WEBHOOK:
    run_webhook(dispatcher=dispatcher)
run_polling(dispatcher=dispatcher, bot=bot)
