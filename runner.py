import asyncio
import ssl

from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiohttp import web

from config.settings import settings

from factories import dp, bot, app, logger

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
from handlers.reg import register_handlers_client

register_handlers_client(dp)


async def bot_start():
    logger.info(f"bot_start: start bot {bot.id}")
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
    loop = asyncio.get_event_loop()
    bot_task = loop.create_task(bot_start())
    web_task = loop.create_task(webserver_start())
    loop.run_until_complete(asyncio.gather(bot_task, web_task))


if __name__ == "__main__":
    main()
