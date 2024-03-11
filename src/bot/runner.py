from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.utils.executor import start_webhook

from settings import settings
from src.bot.factories import dp, bot, logger
from src.bot.handlers.reg import register_handlers_client

# register middleware
dp.middleware.setup(LoggingMiddleware())
# register command

register_handlers_client(dp)


async def on_startup(_) -> None:
    await bot.set_webhook(settings.WEBHOOK_URL)


async def on_shutdown(_) -> None:
    # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()
    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()


def bot_start_webhook():
    logger.info(f"bot_start_webhook: start bot {bot.id}")
    start_webhook(
        dispatcher=dp,
        webhook_path=f"{settings.WEBHOOK_HOST}/{settings.WEBHOOK_PATH}",
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=settings.WEBHOOK_PORT,
    )


def bot_start_polling():
    logger.info(f"bot_start_polling: start bot {bot.id}")
    executor.start_polling(dp, skip_updates=True)
