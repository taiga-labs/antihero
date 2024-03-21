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

                if game_state.player_l.in_game or game_state.player_r.in_game:
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

                    await player_dao.edit_by_id(
                        id=game.player_l_id, score=game_state.player_l.score
                    )
                    await player_dao.edit_by_id(
                        id=game.player_r_id, score=game_state.player_r.score
                    )
                    await db_session.commit()

                    if game_state.player_l.score > game_state.player_r.score:
                        await game_winner_determined(
                            w_nft=game.player_l.nft, l_nft=game.player_r.nft
                        )
                    elif game_state.player_l.score < game_state.player_r.score:
                        await game_winner_determined(
                            w_nft=game.player_r.nft, l_nft=game.player_l.nft
                        )
                    else:
                        await game_draw(
                            nft_d1=game.player_l.nft, nft_d2=game.player_r.nft
                        )
                elif (
                    int(time.time()) - game_state.start_time == 600
                ):  # warning on 10 min left
                    game_data = await game_dao.get_by_params(uuid=game_uuid)
                    game = game_data[0]

                    if game_state.player_l.attempts > 0:
                        await bot.send_message(
                            chat_id=game.player_l.nft.user.telegram_id,
                            text=f"    ⚠️ Предупреждение ⚠️\n"
                            f"Игра завершится через 5 минут.\n"
                            f"{game.player_l.nft.name_nft} [LVL {game.player_l.nft.rare}] vs {game.player_r.nft.name_nft} [LVL {game.player_r.nft.rare}]\n\n"
                            f"Осталось попыток: {game_state.player_l.attempts}",
                        )
                    if game_state.player_r.attempts > 0:
                        await bot.send_message(
                            chat_id=game.player_r.nft.user.telegram_id,
                            text=f"    ⚠️ Предупреждение ⚠️"
                            f"Игра завершится через 5 минут.\n"
                            f"{game.player_l.nft.name_nft} [LVL {game.player_l.nft.rare}] vs {game.player_r.nft.name_nft} [LVL {game.player_r.nft.rare}]\n\n"
                            f"Осталось попыток: {game_state.player_r.attempts}",
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
