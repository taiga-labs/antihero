from aiohttp import web

from settings import settings
from .webapp import app

# TODO logging
web.run_app(app=app, host="0.0.0.0", port=settings.MINIAPP_PORT)
