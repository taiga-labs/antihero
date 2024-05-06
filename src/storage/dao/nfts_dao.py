from sqlalchemy import update, select, func, not_
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

    async def get_by_level_pass(self, user_id: int, op_lvl: int) -> list:
        sql = select(self.model).where(self.model.user_id == user_id,
                                       self.model.activated == True,
                                       func.abs(self.model.rare - op_lvl) <= 3
                                       )
        data = await self.session.execute(sql)
        return list(data.scalars().all())

    async def get_opponent(self, user_id: int, lvl: int) -> Nft | None:
        sql = (select(self.model).order_by(func.random()).where(self.model.duel == True,
                                                                self.model.arena == False,
                                                                not_(self.model.user_id.in_([user_id])),
                                                                func.abs(self.model.rare - lvl) <= 3
                                                                ))
        data = await self.session.execute(sql)
        return data.scalar()
