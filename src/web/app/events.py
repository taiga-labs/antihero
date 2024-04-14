import json

import socketio
from aiogram import Bot, types
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from settings import settings
from src.storage.dao.players_dao import PlayerDAO
from src.storage.driver import get_redis_async_client, async_session
from src.storage.schemas import GameState

from src.web.app import get_bot
from src.web.app.models import AuthModel, GameConnectionModel, ScoreModel
from src.web.app.utils import authentication
from src.web.logger import web_logger


class SocketWrapper:
    def __init__(self):
        self.sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
        self.redis_socket_sessions = {}
        self.redis_game_sessions = {}

    def setup(self):
        self.events()

    def events(self):
        @self.sio.event
        async def connect(sid, environ, auth):
            # validate received data
            try:
                auth_data = AuthModel(
                    data_check_string=auth["data_check_string"],
                    hash=auth["hash"],
                )
            except ValidationError as ve:
                web_logger.error(f"connect | validation error: {ve}")
                await self.sio.disconnect(sid=sid)
                return

            # telegram MiniApp authentication
            if not authentication(
                data_check_string=auth_data.data_check_string, hash=auth_data.hash
            ):
                await self.sio.disconnect(sid=sid)
                web_logger.error(f"connect | auth failed | sid: {sid}")
                return

            self.redis_socket_sessions[sid] = await get_redis_async_client(
                url=settings.GAME_CONNECTION_BROKER_URL
            )
            self.redis_game_sessions[sid] = await get_redis_async_client(
                url=settings.GAME_BROKER_URL
            )
            web_logger.info(f"connect | socket connection open | sid: {sid}")

        @self.sio.on("init_game")
        async def init_game(sid, data):
            # validate received data
            try:
                game_connection = GameConnectionModel(
                    player_id=data["player_id"],
                    uuid=data["uuid"],
                    query_id=data["query_id"]
                )
            except ValidationError as ve:
                web_logger.error(f"init_game | validation error: {ve}")
                await self.sio.disconnect(sid=sid)
                return

            db_session: AsyncSession = async_session()
            player_dao = PlayerDAO(db_session)
            await player_dao.edit_by_id(id=game_connection.player_id, played=True)
            await db_session.commit()
            await db_session.close()

            # broker sessions
            connections_client = self.redis_socket_sessions[sid]
            game_client = self.redis_game_sessions[sid]

            # add new connection state
            await connections_client.set(
                name=sid, value=json.dumps(game_connection.model_dump())
            )

            # get game state by uuid from new connection
            game_state_raw = await game_client.get(name=game_connection.uuid)
            game_state = GameState.model_validate_json(game_state_raw)

            # set 'in game' state
            if game_connection.player_id == game_state.player_l.player_id:
                game_state.player_l.sid = sid
            else:
                game_state.player_r.sid = sid

            await game_client.set(
                name=game_connection.uuid, value=json.dumps(game_state.model_dump())
            )

        @self.sio.on("score")
        async def score(sid, data):
            # validate received data
            try:
                score_data = ScoreModel(
                    score=data["score"],
                )
            except ValidationError as ve:
                web_logger.error(f"score | validation error: {ve}")
                await self.sio.disconnect(sid=sid)
                return

            # broker sessions
            connections_client = self.redis_socket_sessions[sid]
            game_client = self.redis_game_sessions[sid]

            game_connection_raw = await connections_client.get(name=sid)
            game_connection = GameConnectionModel.model_validate_json(
                game_connection_raw
            )
            game_state_raw = await game_client.get(name=game_connection.uuid)
            game_state = GameState.model_validate_json(game_state_raw)

            # update score
            if game_connection.player_id == game_state.player_l.player_id:
                game_state.player_l.score = score_data.score
            else:
                game_state.player_r.score = score_data.score

            await game_client.set(
                name=game_connection.uuid, value=json.dumps(game_state.model_dump())
            )

        @self.sio.event
        async def disconnect(sid):
            web_logger.info(f"disconnect | socket connection closed | sid: {sid}")
            if (sid not in self.redis_socket_sessions) or (
                sid not in self.redis_game_sessions
            ):
                return

            # broker sessions
            connections_client = self.redis_socket_sessions[sid]
            game_client = self.redis_game_sessions[sid]

            game_connection_raw = await connections_client.get(name=sid)
            game_connection = GameConnectionModel.model_validate_json(
                game_connection_raw
            )
            game_state_raw = await game_client.get(name=game_connection.uuid)
            game_state = GameState.model_validate_json(game_state_raw)

            if game_connection.player_id == game_state.player_l.player_id:
                game_state.player_l.sid = None
                total_score = game_state.player_l.score
            else:
                game_state.player_r.sid = None
                total_score = game_state.player_r.score
            await game_client.set(
                name=game_connection.uuid, value=json.dumps(game_state.model_dump())
            )
            await game_client.close()
            del self.redis_game_sessions[sid]
            await connections_client.delete(sid)
            await connections_client.close()
            del self.redis_socket_sessions[sid]

            bot: Bot = await get_bot()
            exit_text = (
                f"📵 Потеряно соединение с игрой #{game_connection.uuid.rsplit('-', 1)[-1]}\nОбщий счет: {total_score}\n\n"
                f"Ожидание результатов соперника..."
            )
            result = types.InlineQueryResultArticle(
                id=game_connection.query_id,
                title="Score",
                input_message_content=types.InputTextMessageContent(
                    message_text=exit_text
                ),
            )
            await bot.answer_web_app_query(
                web_app_query_id=game_connection.query_id, result=result
            )

        @self.sio.on("pure_disconnect")
        async def pure_disconnect(sid):
            web_logger.info(f"pure_disconnect | socket connection closed | sid: {sid}")

            # broker sessions
            connections_client = self.redis_socket_sessions[sid]
            game_client = self.redis_game_sessions[sid]

            game_connection_raw = await connections_client.get(name=sid)
            game_connection = GameConnectionModel.model_validate_json(
                game_connection_raw
            )
            game_state_raw = await game_client.get(name=game_connection.uuid)
            game_state = GameState.model_validate_json(game_state_raw)

            if game_connection.player_id == game_state.player_l.player_id:
                game_state.player_l.sid = None
                total_score = game_state.player_l.score
            else:
                game_state.player_r.sid = None
                total_score = game_state.player_r.score
            await game_client.set(
                name=game_connection.uuid, value=json.dumps(game_state.model_dump())
            )
            await game_client.close()
            del self.redis_game_sessions[sid]
            await connections_client.close()
            del self.redis_socket_sessions[sid]

            bot: Bot = await get_bot()
            exit_text = (
                f"⚡ Игра #{game_connection.uuid.rsplit('-', 1)[-1]} завершена\nОбщий счет: {total_score}\n\n"
                f"Ожидание результатов соперника..."
            )
            result = types.InlineQueryResultArticle(
                id=game_connection.query_id,
                title="Score",
                input_message_content=types.InputTextMessageContent(
                    message_text=exit_text
                ),
            )
            await bot.answer_web_app_query(
                web_app_query_id=game_connection.query_id, result=result
            )
