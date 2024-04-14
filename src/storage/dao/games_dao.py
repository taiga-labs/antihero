from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.base import BaseDAO
from src.storage.models import Game


class GameDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=Game):
        super().__init__(model, session)

    async def get_status(self, uuid: str) -> int:
        data = await self.get_by_params(uuid=uuid)
        if data:
            return 1 if data[0].closed else 0
        return -1

    async def get_active(self) -> list:
        return await self.get_by_params(active=True)

    async def edit_by_uuid(self, uuid: str, **params) -> None:
        sql = update(self.model).where(self.model.uuid == uuid).values(**params)
        await self.session.execute(sql)
