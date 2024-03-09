from aiohttp import web
from aiohttp.web_fileresponse import FileResponse

from settings import settings
from src.bot.factories import bot
from src.web.routes import routes

app = web.Application()
app["bot"] = bot

if settings.DEV:
    @routes.get("/")
    async def index(request):
        return FileResponse("web/static/index.html")

    app.router.add_static(prefix='/static', path='web/static')

app.add_routes(routes)


