from flask import Response

from src.web import web_logger, app
from flask_cors import cross_origin


@app.route("/auth")
@cross_origin()
async def auth(request):
    web_logger.info("IN AUTH")
    try:
        data = await request.json()
        d = data["data_check_string"]
        hash = data["hash"]
    except:
        return Response(status=403)
    return Response(status=200)


@app.route("/preinfo")
@cross_origin()
async def preinfo(request):
    try:
        data = await request.json()
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
    except:
        return Response(status=403)
    body = {
        "score": 0,
        "attempts": 0,
    }
    return body


@app.route("/start")
@cross_origin()
async def start(request):
    try:
        data = await request.json()
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
    except:
        return Response(status=403)
    return Response(status=200)


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
        return Response(status=403)
    return Response(status=200)
