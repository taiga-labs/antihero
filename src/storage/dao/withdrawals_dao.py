from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.base import BaseDAO
from src.storage.models import Withdrawal


class WithdrawalDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=Withdrawal):
        super().__init__(model, session)

    async def get_active(self) -> list:
        return await self.get_by_params(active=True)

    async def close(self, id: int) -> None:
        await self.edit_by_id(id=id, active=False)
