from fastapi import status, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.games_dao import GameDAO
from src.storage.driver import async_session

router = APIRouter()


def get_session_local():
    yield async_session()


@router.get("/game_status")
async def game_status(uuid: str, player_id: int, db_session: AsyncSession = Depends(get_session_local)):
    game_dao = GameDAO(db_session)
    game_data = await game_dao.get_by_params(uuid=uuid)
    await db_session.close()

    if not game_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Игра недоступна",
        )

    game = game_data[0]
    if game.player_l.id == player_id:
        played = game.player_l.played
    elif game.player_r.id == player_id:
        played = game.player_r.played
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Игра недоступна",
        )

    if played:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Игра была завершена",
        )
