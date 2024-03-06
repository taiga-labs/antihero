from aiohttp import web

from bot.factories import bot
from web.routes import routes

app = web.Application()
app["bot"] = bot
app.add_routes(routes)
app.router.add_static(prefix='/static', path='web/static')
