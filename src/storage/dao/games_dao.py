from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.base import BaseDAO
from src.storage.models import Game


class GameDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=Game):
        super().__init__(model, session)

    async def is_closed(self, uuid: str) -> bool:
        data = await self.get_by_params(uuid=uuid)
        return data[0].closed

    async def get_active(self) -> list:
        return await self.get_by_params(active=True)

    async def edit_by_uuid(self, uuid: str, **params) -> None:
        sql = update(self.model).where(self.model.uuid == uuid).values(**params)
        await self.session.execute(sql)
