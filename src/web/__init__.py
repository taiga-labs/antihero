import logging
import aiohttp_cors
import socketio
from aiohttp import web

from src.bot.factories import bot

app = web.Application()
app["bot"] = bot

# cors = aiohttp_cors.setup(
#     app,
#     defaults={
#         "*": aiohttp_cors.ResourceOptions(
#             allow_credentials=True, expose_headers="*", allow_headers="*"
#         )
#     },
# )
#
# for route in list(app.router.routes()):
#     cors.add(route)
#
sio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
# sio.attach(app)


logging.basicConfig()
web_logger = logging.getLogger("ANTIHERO_WEB")
web_logger.setLevel(logging.INFO)
