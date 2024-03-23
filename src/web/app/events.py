import json
from settings import settings
from src.storage.driver import get_redis_async_client
from src.storage.schemas import GameState, GameConnection
from src.web import web_logger, sio


@sio.on("connect")
async def connect(sid, data):
    web_logger.info(f"connect | socket connection open | sid: {sid}")


@sio.on("disconnect")
async def disconnect(sid):
    web_logger.info(f"disconnect | socket connection closed | sid: {sid}")
    redis_game_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)
    redis_connection_session = await get_redis_async_client(
        url=settings.GAME_CONNECTION_BROKER_URL
    )

    game_connection_raw = await redis_connection_session.get(name=sid)
    if game_connection_raw:
        game_connection = GameConnection.model_validate_json(game_connection_raw)

        game_state_raw = await redis_game_session.get(name=game_connection.uuid)
        game_state = GameState.model_validate_json(game_state_raw)

        if game_connection.player_id == game_state.player_l.player_id:
            game_state.player_l.sid = None
        else:
            game_state.player_r.sid = None

        await redis_game_session.set(
            name=game_connection.uuid, value=json.dumps(game_state.model_dump())
        )
        await redis_connection_session.delete(sid)
    await redis_game_session.close()
    await redis_connection_session.close()


@sio.on("set_connection")
async def set_connection(sid, data):
    web_logger.info(f"set_connection | socket set connection data | sid: {sid}")
    redis_game_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)
    redis_connection_session = await get_redis_async_client(
        url=settings.GAME_CONNECTION_BROKER_URL
    )

    game_connection = GameConnection(
        player_id=data["player_id"],
        uuid=data["uuid"],
    )
    await redis_connection_session.set(
        name=sid, value=json.dumps(game_connection.model_dump())
    )

    game_state_raw = await redis_game_session.get(name=game_connection.uuid)
    game_state = GameState.model_validate_json(game_state_raw)

    if game_connection.player_id == game_state.player_l.player_id:
        game_state.player_l.sid = sid
    else:
        game_state.player_r.sid = sid

    await redis_game_session.set(
        name=game_connection.uuid, value=json.dumps(game_state.model_dump())
    )
    await redis_game_session.close()
    await redis_connection_session.close()
