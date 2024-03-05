import asyncio
import ssl

from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook
from aiohttp import web

from config.settings import settings

from factories import dp, bot, app, logger

WEBHOOK_URL = f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}"

# register middleware
dp.middleware.setup(LoggingMiddleware())
# register command
from handlers.reg import register_handlers_client

register_handlers_client(dp)


async def on_startup(_) -> None:
    await bot.set_webhook(WEBHOOK_URL)


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
        webhook_path=WEBHOOK_URL,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=settings.WEBAPP_HOST,
        port=int(settings.WEBAPP_PORT),
    )


async def bot_start_polling():
    logger.info(f"bot_start_polling: start bot {bot.id}")
    await dp.start_polling(bot)


async def webserver_start():
    runner = web.AppRunner(app)
    await runner.setup()
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile='web/static/certs/YOURPUBLIC.pem',
                                keyfile='web/static/certs/YOURPRIVATE.key')
    logger.info(f"webserver_start: start web app on {settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}")
    site = web.TCPSite(runner, settings.WEBAPP_HOST, settings.WEBAPP_PORT, ssl_context=ssl_context)
    await site.start()


def main():
    if settings.DEV:
        loop = asyncio.get_event_loop()
        bot_task = loop.create_task(bot_start_polling())
        web_task = loop.create_task(webserver_start())
        loop.run_until_complete(asyncio.gather(bot_task, web_task))
        asyncio.run(bot_start_polling())
    else:
        bot_start_webhook()


if __name__ == "__main__":
    main()
