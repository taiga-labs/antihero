from fastapi import status, APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.games_dao import GameDAO
from src.storage.driver import async_session
from src.web.app.models import StatusModel

router = APIRouter()


@router.get(
    "/game_status",
    response_model=StatusModel,
    response_model_exclude_unset=True
)
async def game_status(data: StatusModel, db_session: AsyncSession = Depends(async_session)):
    game_dao = GameDAO(db_session)
    if await game_dao.is_closed(uuid=data.uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Игра была завершена",
        )
