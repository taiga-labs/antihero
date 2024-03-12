import asyncio
import time

from sqlalchemy.ext.asyncio import AsyncSession

from src.services import processor_logger
from src.storage.dao.games_dao import GameDAO
from src.storage.driver import async_session
from src.utils.game import game_winner_determined, game_draw


async def process_games():
    db_session: AsyncSession = async_session()

    try:
        game_dao = GameDAO(db_session)

        while True:
            active_games = await game_dao.get_active()

            if not len(active_games):
                continue

            for game in active_games:
                if game.player_l.score is not None and game.player_r.score is not None:
                    processor_logger.info(f"process_games | game over: {game.uuid}")
                    if game.player_l.score > game.player_r.score:
                        await game_winner_determined(
                            w_nft=game.player_l.nft, l_nft=game.player_r.nft
                        )
                    elif game.player_l.score < game.player_r.score:
                        await game_winner_determined(
                            w_nft=game.player_r.nft, l_nft=game.player_l.nft
                        )
                    else:
                        await game_draw(
                            nft_d1=game.player_l.nft, nft_d2=game.player_r.nft
                        )
                    await game_dao.edit_by_id(id=game.id, active=False)
                    await db_session.commit()

                if game.exp_time < int(time.time()):
                    processor_logger.info(f"process_games | game expired: {game.uuid}")
                    if game.player_l.score is not None:
                        await game_winner_determined(
                            w_nft=game.player_l.nft, l_nft=game.player_r.nft
                        )
                    elif game.player_r.score is not None:
                        await game_winner_determined(
                            w_nft=game.player_r.nft, l_nft=game.player_l.nft
                        )
                    else:
                        await game_draw(
                            nft_d1=game.player_l.nft, nft_d2=game.player_r.nft
                        )
                    await game_dao.edit_by_id(id=game.id, active=False)
                    await db_session.commit()

            await asyncio.sleep(1)
    finally:
        processor_logger.info("process_games | close game processor")
        await db_session.close()


if __name__ == "__main__":
    try:
        processor_logger.info("Start game processor...")
        asyncio.run(process_games())
    except KeyboardInterrupt:
        exit(0)
