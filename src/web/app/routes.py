from flask import Response, jsonify

from src.web import web_logger, app
from flask_cors import cross_origin


@app.route("/auth", methods=["OPTIONS", "POST"])
@cross_origin()
async def auth(request):
    web_logger.info("IN AUTH")
    try:
        data = await request.json()
        d = data["data_check_string"]
        hash = data["hash"]
        response = Response(status=200)
    except:
        response = Response(status=403)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "append,delete,entries,foreach,get,has,keys,set,values,Authorization"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response


@app.route("/preinfo")
@cross_origin()
async def preinfo(request):
    try:
        data = await request.json()
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
        body = {"score": 0, "attempts": 0}
        response = jsonify(body)
    except:
        response = Response(status=403)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "append,delete,entries,foreach,get,has,keys,set,values,Authorization"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response


@app.route("/start")
@cross_origin()
async def start(request):
    try:
        data = await request.json()
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
        response = Response(status=200)
    except:
        response = Response(status=403)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "append,delete,entries,foreach,get,has,keys,set,values,Authorization"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response


@app.route("/score")
@cross_origin()
async def score(request):
    try:
        data = await request.json()
        query_id = data["query_id"]
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
        score = int(data["score"])
        response = Response(status=200)
    except:
        response = Response(status=403)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "append,delete,entries,foreach,get,has,keys,set,values,Authorization"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response
