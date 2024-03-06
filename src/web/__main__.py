import ssl

from aiohttp import web

from settings import settings
from .webapp import app

ssl_context = None
if settings.DEV:
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=settings.CERT_FILE_PATH,
                                keyfile=settings.KEY_FILE_PATH)

web.run_app(app=app,
            host=settings.MINIAPP_HOST,
            port=settings.MINIAPP_PORT,
            ssl_context=ssl_context)
