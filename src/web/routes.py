import hmac
import hashlib
import pickle
from urllib import parse

from aiogram import Bot, types
from aiohttp import web

from settings import settings
from src.storage.driver import get_redis_async_client
from src.storage.schemas import GameState
from src.web import web_logger

routes = web.RouteTableDef()


@routes.post("/auth")
async def auth(request):
    data = await request.json()
    data_check_string = parse.unquote(data["data_check_string"])
    hash = data["hash"]

    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=settings.TELEGRAM_API_KEY.get_secret_value().encode(),
        digestmod=hashlib.sha256,
    )

    hash_check = hmac.new(
        key=secret_key.digest(),
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    )

    if hash_check.hexdigest() == hash:
        return web.Response(status=200)
    return web.Response(status=403)


@routes.post("/preinfo")
async def preinfo(request):
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    data = await request.json()
    game_uuid = data["uuid"]
    player_id = int(data["player_id"])

    if not await redis_session.exists(game_uuid):
        web_logger.info(
            f"preinfo | game ({game_uuid}) : player ({player_id}) | access denied | game closed"
        )
        return web.Response(status=403, text="Игра завершена")

    game_state_raw = await redis_session.get(name=game_uuid)
    game_state: GameState = pickle.loads(game_state_raw)

    player = (
        game_state.player_l
        if player_id == game_state.player_l.player_id
        else game_state.player_r
    )

    body = {
        "score": player.score if player.score else 0,
        "attempts": player.attempts,
    }

    return web.Response(status=200, body=body)


@routes.post("/start")
async def start(request):
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    data = await request.json()
    game_uuid = data["uuid"]
    player_id = int(data["player_id"])

    if not await redis_session.exists(game_uuid):
        web_logger.info(
            f"preinfo | game ({game_uuid}) : player ({player_id}) | access denied | game closed"
        )
        return web.Response(status=403, text="Игра завершена")

    game_state_raw = await redis_session.get(name=game_uuid)
    game_state: GameState = pickle.loads(game_state_raw)

    player = (
        game_state.player_l
        if player_id == game_state.player_l.player_id
        else game_state.player_r
    )

    if player.attempts == 0:
        web_logger.info(
            f"start | game ({game_uuid}) : player ({player_id}) | access denied | attemption limit"
        )
        return web.Response(status=403, text="Исчерпано количество попыток")

    web_logger.info(f"start | game ({game_uuid}) : player ({player_id}) | start game")

    if player_id == game_state.player_l.player_id:
        game_state.player_l.attempts = game_state.player_l.attempts - 1
        game_state.player_l.active = True
    else:
        game_state.player_r.attempts = game_state.player_r.attempts - 1
        game_state.player_r.active = True
    await redis_session.set(name=game_uuid, value=pickle.dumps(game_state))

    return web.Response(status=200)


@routes.post("/score")
async def score(request):
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    bot: Bot = request.app["bot"]

    data = await request.json()
    query_id = data["query_id"]
    game_uuid = data["uuid"]
    player_id = int(data["player_id"])
    score = int(data["score"])

    if not await redis_session.exists(game_uuid):
        web_logger.info(
            f"preinfo | game ({game_uuid}) : player ({player_id}) | access denied | game closed"
        )
        return web.Response(status=403, text="Игра завершена")

    game_state_raw = await redis_session.get(name=game_uuid)
    game_state: GameState = pickle.loads(game_state_raw)

    if player_id == game_state.player_l.player_id:
        game_state.player_l.score = score
        game_state.player_l.active = False
        attempts = game_state.player_l.attempts
    else:
        game_state.player_r.score = score
        game_state.player_r.active = False
        attempts = game_state.player_r.attempts

    await redis_session.set(name=game_uuid, value=pickle.dumps(game_state))

    if not attempts:
        result_text = (
            f"Игра: {game_uuid}\nТвой счет: {score} очков\n\n"
            f"Ожидание результатов соперника..."
        )
    else:
        result_text = f"Игра: {game_uuid}\nТвой счет: {score} очков\n"

    result = types.InlineQueryResultArticle(
        id=query_id,
        title="Score",
        input_message_content=types.InputTextMessageContent(message_text=result_text),
    )
    await bot.answer_web_app_query(query_id, result)
