from aiogram.utils import executor
from aiogram.utils.executor import start_webhook
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from config.settings import settings

from create_bot import dp, bot


WEBHOOK_URL = f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}"


async def on_startup(_) -> None:
    await bot.set_webhook(WEBHOOK_URL, certificate=open(settings.PATH_CERT, 'r'))


async def on_shutdown(_) -> None:
    # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()
    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()


# register middleware
dp.middleware.setup(LoggingMiddleware())
# register command
from handler.reg import register_handlers_client

register_handlers_client(dp)

# run bot
if settings.DEV:
    executor.start_polling(dp, skip_updates=True)  # start bot via polling
elif not settings.DEV:  # start bot via webhook
    start_webhook(
        dispatcher=dp,
        webhook_path=settings.WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=settings.WEBHOOK_HOST,
        port=settings.WEBHOOK_PORT,
    )
