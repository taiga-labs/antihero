from aiohttp import web

from src.web import web_logger, app
from flask_cors import cross_origin


# router = web.RouteTableDef()


@app.route("/auth")
@cross_origin()
async def auth(request):
    web_logger.info("IN AUTH")
    try:
        data = await request.json()
        d = data["data_check_string"]
        hash = data["hash"]
    except:
        return web.Response(status=403)
    return web.Response(status=200)


@app.route("/preinfo")
@cross_origin()
async def preinfo(request):
    try:
        data = await request.json()
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
    except:
        return web.Response(status=403)
    body = {
        "score": 0,
        "attempts": 0,
    }
    return web.json_response(body)


@app.route("/start")
@cross_origin()
async def start(request):
    try:
        data = await request.json()
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
    except:
        return web.Response(status=403)
    return web.Response(status=200)


@app.route("/score")
@cross_origin()
async def score(request):
    try:
        data = await request.json()
        query_id = data["query_id"]
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
        score = int(data["score"])
    except:
        return web.Response(status=403)
    return web.Response(status=200)
