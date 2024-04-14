from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.base import BaseDAO
from src.storage.models import Game


class GameDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=Game):
        super().__init__(model, session)
