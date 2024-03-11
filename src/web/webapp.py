from aiohttp import web
import aiohttp_cors

from src.bot.factories import bot
from src.web.routes import routes

app = web.Application()
app["bot"] = bot
app.add_routes(routes)

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

for route in list(app.router.routes()):
    cors.add(route)
