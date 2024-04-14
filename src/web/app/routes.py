from fastapi import status, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.games_dao import GameDAO
from src.storage.driver import async_session

router = APIRouter()


@router.get("/game_status")
async def game_status(uuid: str, db_session: AsyncSession = Depends(async_session)):
    game_dao = GameDAO(db_session)
    if await game_dao.is_closed(uuid=uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Игра была завершена",
        )
