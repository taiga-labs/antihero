import aiohttp_cors
from aiohttp import web

from settings import settings
from src.web import app, web_logger, sio

from src.web.app.routes import router

cors = aiohttp_cors.setup(app)
app.add_routes(router)

for resource in app.router._resources:
    # Because socket.io already adds cors, if you don't skip socket.io, you get error saying, you've done this already.
    if resource.raw_match("/socket.io/"):
        continue
    cors.add(
        resource,
        {
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*"
            )
        },
    )

sio.attach(app)

web_logger.info(f"Runnings web app | HOST:0.0.0.0 PORT:{settings.MINIAPP_PORT}")
web.run_app(app=app, host="0.0.0.0", port=settings.MINIAPP_PORT)
