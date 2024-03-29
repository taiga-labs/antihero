import hmac
import hashlib
import json
from urllib import parse

from aiogram import Bot, types
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from starlette import status

from settings import settings
from src.storage.driver import get_redis_async_client
from src.storage.schemas import GameState

from src.web import web_logger
from src.web.app import get_bot
from src.web.app.models import AuthModel, IDsModel, ScoreModel


router = APIRouter()


@router.post("/auth")
async def auth(data: AuthModel):
    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=settings.TELEGRAM_API_KEY.get_secret_value().encode(),
        digestmod=hashlib.sha256,
    )

    hash_check = hmac.new(
        key=secret_key.digest(),
        msg=data.data_check_string.encode(),
        digestmod=hashlib.sha256,
    )

    if hash_check.hexdigest() != hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authentication failed",
        )


@router.post("/preinfo")
async def preinfo(data: IDsModel):
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    if not await redis_session.exists(data.uuid):
        web_logger.info(
            f"preinfo | game ({data.uuid}) : player ({data.player_id}) | access denied | game closed"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Игра завершена",
        )

    game_state_raw = await redis_session.get(name=data.uuid)
    game_state = GameState.model_validate_json(game_state_raw)

    player = (
        game_state.player_l
        if data.player_id == game_state.player_l.player_id
        else game_state.player_r
    )

    await redis_session.close()
    body = {
        "score": player.score,
        "attempts": player.attempts,
    }
    return body


@router.post("/start")
async def start(data: IDsModel):
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    if not await redis_session.exists(data.uuid):
        web_logger.info(
            f"start | game ({data.uuid}) : player ({data.player_id}) | access denied | game closed"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Игра завершена",
        )

    game_state_raw = await redis_session.get(name=data.uuid)
    game_state = GameState.model_validate_json(game_state_raw)

    player = (
        game_state.player_l
        if data.player_id == game_state.player_l.player_id
        else game_state.player_r
    )

    if player.attempts == 0:
        web_logger.info(
            f"start | game ({data.uuid}) : player ({data.player_id}) | access denied | attemption limit"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Исчерпано количество попыток",
        )

    web_logger.info(f"start | game ({data.uuid}) : player ({data.player_id}) | start game")

    if data.player_id == game_state.player_l.player_id:
        game_state.player_l.attempts = game_state.player_l.attempts - 1
    else:
        game_state.player_r.attempts = game_state.player_r.attempts - 1
    await redis_session.set(name=data.uuid, value=json.dumps(game_state.model_dump()))
    await redis_session.close()


@router.post("/score")
async def score(data: ScoreModel, bot: Bot = Depends(get_bot)):
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    if not await redis_session.exists(data.uuid):
        web_logger.info(
            f"score | game ({data.uuid}) : player ({data.player_id}) | access denied | game closed"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Игра завершена",
        )

    game_state_raw = await redis_session.get(name=data.uuid)
    game_state = GameState.model_validate_json(game_state_raw)

    if data.player_id == game_state.player_l.player_id:
        game_state.player_l.score += data.score
        total_score = game_state.player_l.score
        attempts = game_state.player_l.attempts
    else:
        game_state.player_r.score += data.score
        total_score = game_state.player_r.score
        attempts = game_state.player_r.attempts

    await redis_session.set(name=data.uuid, value=json.dumps(game_state.model_dump()))

    if not attempts:
        exit_text = (
            f"Игра #{data.uuid.rsplit('-', 1)[-1]}\nОбщий счет: {total_score}\n\n"
            f"Ожидание результатов соперника..."
        )
        result = types.InlineQueryResultArticle(
            id=data.query_id,
            title="Score",
            input_message_content=types.InputTextMessageContent(message_text=exit_text),
        )
        await bot.answer_web_app_query(web_app_query_id=data.query_id, result=result)
    await redis_session.close()
