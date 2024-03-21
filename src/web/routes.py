import hmac
import hashlib
import json
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
    return web.Response(status=200)


@routes.post("/preinfo")
async def preinfo(request):
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    data = await request.json()
    game_uuid = data["uuid"]  # TODO check if exists
    player_id = int(data["player_id"])

    if not await redis_session.exists(game_uuid):
        web_logger.info(
            f"preinfo | game ({game_uuid}) : player ({player_id}) | access denied | game closed"
        )
        return web.Response(status=403, text="Игра завершена")

    game_state_raw = await redis_session.get(name=game_uuid)
    game_state = GameState.model_validate_json(game_state_raw)

    player = (
        game_state.player_l
        if player_id == game_state.player_l.player_id
        else game_state.player_r
    )

    body = {
        "score": player.score,
        "attempts": player.attempts,
    }
    return web.json_response(body)


@routes.post("/start")
async def start(request):
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    data = await request.json()
    game_uuid = data["uuid"]
    player_id = int(data["player_id"])

    if not await redis_session.exists(game_uuid):
        web_logger.info(
            f"start | game ({game_uuid}) : player ({player_id}) | access denied | game closed"
        )
        return web.Response(status=403, text="Игра завершена")

    game_state_raw = await redis_session.get(name=game_uuid)
    game_state = GameState.model_validate_json(game_state_raw)

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
        game_state.player_l.in_game = True
    else:
        game_state.player_r.attempts = game_state.player_r.attempts - 1
        game_state.player_r.in_game = True
    await redis_session.set(name=game_uuid, value=json.dumps(game_state.model_dump()))
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
            f"score | game ({game_uuid}) : player ({player_id}) | access denied | game closed"
        )
        return web.Response(status=403, text="Игра завершена")

    game_state_raw = await redis_session.get(name=game_uuid)
    game_state = GameState.model_validate_json(game_state_raw)

    if player_id == game_state.player_l.player_id:
        game_state.player_l.score += score
        total_score = game_state.player_l.score
        game_state.player_l.in_game = False
        attempts = game_state.player_l.attempts
    else:
        game_state.player_r.score += score
        total_score = game_state.player_r.score
        game_state.player_r.in_game = False
        attempts = game_state.player_r.attempts

    await redis_session.set(name=game_uuid, value=json.dumps(game_state.model_dump()))

    if not attempts:
        exit_text = (
            f"Игра: {game_uuid}\nОбщий счет: {total_score}\n\n"
            f"Ожидание результатов соперника..."
        )
        result = types.InlineQueryResultArticle(
            id=query_id,
            title="Score",
            input_message_content=types.InputTextMessageContent(message_text=exit_text),
        )
        await bot.answer_web_app_query(web_app_query_id=query_id, result=result)

    return web.Response(status=200)
