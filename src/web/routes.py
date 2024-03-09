import hmac
import hashlib
from urllib import parse

from aiogram import Bot, types
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from settings import settings
from src.storage.dao.games_dao import GameDAO
from src.storage.dao.players_dao import PlayerDAO
from src.storage.driver import async_session

routes = web.RouteTableDef()


@routes.post("/auth")
async def auth(request):
    data = await request.json()
    data_check_string = parse.unquote(data['data_check_string'])
    hash = data['hash']

    secret_key = hmac.new(key="WebAppData".encode(),
                          msg=settings.TELEGRAM_API_KEY.get_secret_value().encode(),
                          digestmod=hashlib.sha256)

    hash_check = hmac.new(key=secret_key.digest(),
                          msg=data_check_string.encode(),
                          digestmod=hashlib.sha256)

    if hash_check.hexdigest() == hash:
        return web.Response(status=200)
    return web.Response(status=403)


@routes.post('/start')
async def start(request):
    db_session: AsyncSession = async_session()
    game_dao = GameDAO(session=db_session)
    player_dao = PlayerDAO(session=db_session)

    data = await request.json()
    game_uuid = data['uuid']
    nft_id = int(data['nft_id'])

    game_data = await game_dao.get_by_params(uuid=game_uuid)
    game = game_data[0]
    if not game.active:
        await db_session.close()
        return web.Response(text="Срок действия игры истек")

    player = game.player_l if game.player_l.nft_id == nft_id else game.player_r if game.player_r.nft_id == nft_id else None
    if not player:
        await db_session.close()
        return web.Response(text="Неизвестный игрок")

    if player.score:
        await db_session.close()
        return web.Response(text="Игра была завершена")

    await player_dao.edit_by_id(id=player.id, score=0)
    await db_session.commit()
    await db_session.close()
    return web.Response(text="allow")


@routes.post('/score')
async def score(request):
    db_session: AsyncSession = async_session()
    game_dao = GameDAO(session=db_session)
    player_dao = PlayerDAO(session=db_session)

    bot: Bot = request.app['bot']

    data = await request.json()
    query_id = data['query_id']
    game_score = int(data['score'])
    game_uuid = data['uuid']
    nft_id = int(data['nft_id'])

    game_data = await game_dao.get_by_params(uuid=game_uuid)
    game = game_data[0]
    if not game.active:
        await db_session.close()
        return web.Response(text="Срок действия игры истек")

    player = game.player_l if game.player_l.nft_id == nft_id else game.player_r if game.player_r.nft_id == nft_id else None
    if not player:
        await db_session.close()
        return web.Response(text="Неизвестный игрок")

    await player_dao.edit_by_id(id=player.id, score=game_score)
    await db_session.commit()

    result_text = (f"Твой счет: {game_score} очков\n"
                   f"Ожидание результатов соперника...")
    result = types.InlineQueryResultArticle(
        id=query_id,
        title='Score',
        input_message_content=types.InputTextMessageContent(message_text=result_text))
    await bot.answer_web_app_query(query_id, result)
