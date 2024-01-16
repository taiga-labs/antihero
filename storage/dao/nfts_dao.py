from sqlalchemy import update, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from storage.dao.base import BaseDAO
from storage.models import Nft


class NftDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=Nft):
        super().__init__(model, session)

    async def edit_by_user_id(self, user_id: int, **params) -> None:
        sql = update(self.model).where(self.model.user_id == user_id).values(**params)
        await self.session.execute(sql)

    async def edit_by_address(self, address: str, **params) -> None:
        sql = update(self.model).where(self.model.addr == address).values(**params)
        await self.session.execute(sql)

    async def delete_by_address(self, address: str) -> None:
        sql = delete(self.model).where(self.model.addr == address)
        await self.session.execute(sql)

    async def get_opponent(self, user_id: str) -> Nft:
        sql = select(self.model).order_by(func.random()).where(self.model.duel == True).filter(self.model.user_id.notlike(user_id))
        data = await self.session.execute(sql)
        return data.scalar_one_or_none()    # TODO check fetchone() or first()
