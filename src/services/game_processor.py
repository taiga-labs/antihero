import asyncio
import time

from sqlalchemy.ext.asyncio import AsyncSession

from settings import settings
from src.bot.factories import bot
from src.services import processor_logger
from src.storage.dao.games_dao import GameDAO
from src.storage.dao.players_dao import PlayerDAO
from src.storage.driver import async_session, get_redis_async_client
from src.storage.schemas import GameState
from src.utils.game import game_winner_determined, game_draw


async def process_games():
    redis_session = await get_redis_async_client(url=settings.GAME_BROKER_URL)

    db_session: AsyncSession = async_session()

    try:
        game_dao = GameDAO(db_session)
        player_dao = PlayerDAO(db_session)

        while True:
            await asyncio.sleep(1)

            game_uuid_keys = await redis_session.keys("*")
            for game_uuid in game_uuid_keys:
                game_state_raw = await redis_session.get(name=game_uuid)
                game_state = GameState.model_validate_json(game_state_raw)

                if game_state.player_l.sid or game_state.player_r.sid:
                    continue

                if (
                    game_state.player_l.attempts == 0
                    and game_state.player_r.attempts == 0
                ) or (
                    int(time.time()) - game_state.start_time >= 900
                ):  # 15 min left
                    processor_logger.info(
                        f"process_games | game over | game: {game_uuid}"
                    )

                    await redis_session.delete(game_uuid)
                    game_data = await game_dao.get_by_params(uuid=game_uuid)
                    game = game_data[0]
                    await db_session.refresh(game)

                    await player_dao.edit_by_id(
                        id=game.player_l_id, score=game_state.player_l.score
                    )
                    await player_dao.edit_by_id(
                        id=game.player_r_id, score=game_state.player_r.score
                    )
                    await db_session.commit()

                    if game_state.player_l.score > game_state.player_r.score:
                        await game_winner_determined(
                            w_nft=game.player_l.nft, w_score=game_state.player_l.score,
                            l_nft=game.player_r.nft, l_score=game_state.player_r.score
                        )
                    elif game_state.player_l.score < game_state.player_r.score:
                        await game_winner_determined(
                            w_nft=game.player_r.nft, w_score=game_state.player_r.score,
                            l_nft=game.player_l.nft, l_score=game_state.player_l.score
                        )
                    else:
                        await game_draw(
                            nft_d1=game.player_l.nft, score_d1=game_state.player_l.score,
                            nft_d2=game.player_r.nft, score_d2=game_state.player_r.score
                        )
                elif (
                    600 <= int(time.time()) - game_state.start_time <= 630
                ):  # warning on 10 min left
                    if game_state.player_l.attempts > 0:
                        game_data = await game_dao.get_by_params(uuid=game_uuid)
                        game = game_data[0]
                        if not game.player_l.notified:
                            await bot.send_message(
                                chat_id=game.player_l.nft.user.telegram_id,
                                text=f"    ⚠️ Предупреждение ⚠️\n"
                                f"Игра #{game.uuid.rsplit('-', 1)[-1]} завершится через 5 минут.\n"
                                f"{game.player_l.nft.name_nft} [LVL {game.player_l.nft.rare}] vs {game.player_r.nft.name_nft} [LVL {game.player_r.nft.rare}]\n\n"
                                f"Осталось попыток: {game_state.player_l.attempts}",
                            )
                            await player_dao.edit_by_id(
                                id=game.player_l_id, notified=True
                            )
                    if game_state.player_r.attempts > 0:
                        game_data = await game_dao.get_by_params(uuid=game_uuid)
                        game = game_data[0]
                        if not game.player_r.notified:
                            await bot.send_message(
                                chat_id=game.player_r.nft.user.telegram_id,
                                text=f"    ⚠️ Предупреждение ⚠️\n"
                                f"Игра #{game.uuid.rsplit('-', 1)[-1]} завершится через 5 минут.\n"
                                f"{game.player_l.nft.name_nft} [LVL {game.player_l.nft.rare}] vs {game.player_r.nft.name_nft} [LVL {game.player_r.nft.rare}]\n\n"
                                f"Осталось попыток: {game_state.player_r.attempts}",
                            )
                            await player_dao.edit_by_id(
                                id=game.player_r_id, notified=True
                            )
    finally:
        processor_logger.info("process_games | close game processor")
        await db_session.close()


if __name__ == "__main__":
    try:
        processor_logger.info("Start game processor...")
        asyncio.run(process_games())
    except KeyboardInterrupt:
        exit(0)
