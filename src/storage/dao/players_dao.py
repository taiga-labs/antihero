from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.base import BaseDAO
from src.storage.models import Player


class PlayerDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=Player):
        super().__init__(model, session)
