from aiohttp import web

router = web.RouteTableDef()


@router.post("/auth")
async def auth(request):
    try:
        data = await request.json()
        d = data["data_check_string"]
        hash = data["hash"]
    except:
        return web.Response(status=403)
    return web.Response(status=200)


@router.post("/preinfo")
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


@router.post("/start")
async def start(request):
    try:
        data = await request.json()
        game_uuid = data["uuid"]
        player_id = int(data["player_id"])
    except:
        return web.Response(status=403)
    return web.Response(status=200)


@router.post("/score")
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
