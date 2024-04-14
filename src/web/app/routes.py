from fastapi import status, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.games_dao import GameDAO
from src.storage.driver import async_session

router = APIRouter()


def get_session_local():
    yield async_session()


@router.get("/game_status")
async def game_status(uuid: str, db_session: AsyncSession = Depends(get_session_local)):
    game_dao = GameDAO(db_session)
    gstat = await game_dao.get_status(uuid=uuid)
    await db_session.close()
    match gstat:
        case -1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Игра недоступна",
            )
        case 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Игра была завершена",
            )
        case _:
            pass
