from fastapi import APIRouter, HTTPException
from starlette import status

from src.web.app.models import AuthModel, IDsModel, ScoreModel

router = APIRouter()


@router.post("/auth")
async def auth(data: AuthModel):
    if not (data.data_check_string and data.hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"",
        )


@router.post("/preinfo")
async def preinfo(data: IDsModel):
    if not (data.uuid and data.player_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"",
        )
    body = {"score": 0, "attempts": 0}
    return body


@router.post("/start")
async def start(data: IDsModel):
    if not (data.uuid and data.player_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"",
        )


@router.post("/score")
async def score(data: ScoreModel):
    if not (data.query_id and data.uuid and data.player_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"",
        )
