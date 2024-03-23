from aiohttp import web

from settings import settings
from src.web import app, web_logger
from src.web.app.routes import router

app.add_routes(router)

web_logger.info(f"Runnings web app | HOST:0.0.0.0 PORT:{settings.MINIAPP_PORT}")
web.run_app(app=app, host="0.0.0.0", port=settings.MINIAPP_PORT)
