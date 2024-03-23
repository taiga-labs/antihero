from aiohttp import web

router = web.RouteTableDef()


@router.post("/auth")
async def auth(request):
    return web.Response(status=200)


@router.post("/preinfo")
async def preinfo(request):
    body = {
        "score": 0,
        "attempts": 0,
    }
    return web.json_response(body)


@router.post("/start")
async def start(request):
    return web.Response(status=200)


@router.post("/score")
async def score(request):
    return web.Response(status=200)
