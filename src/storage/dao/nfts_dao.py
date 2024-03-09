from sqlalchemy import update, select, delete, func, not_
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.base import BaseDAO
from src.storage.models import Nft


class NftDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=Nft):
        super().__init__(model, session)

    async def is_exists(self, address: str) -> bool:
        data = await self.get_by_params(address=address)
        if data:
            return True
        return False

    async def edit_by_address(self, address: str, **params) -> None:
        sql = update(self.model).where(self.model.address == address).values(**params)
        await self.session.execute(sql)

    async def get_opponent(self, user_id: int) -> Nft | None:
        sql = select(self.model).order_by(func.random()).where(self.model.duel == True,
                                                               self.model.arena == False,
                                                               not_(self.model.user_id.in_([user_id])))
        data = await self.session.execute(sql)
        return data.scalar()
