from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.dao.base import BaseDAO
from src.storage.models import User


class UserDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=User):
        super().__init__(model, session)

    async def is_exists(self, telegram_id) -> bool:
        data = await self.get_by_params(telegram_id=telegram_id)
        if data:
            return True
        return False

    async def edit_by_telegram_id(self, telegram_id: int, **params) -> None:
        sql = (
            update(self.model)
            .where(self.model.telegram_id == telegram_id)
            .values(**params)
        )
        await self.session.execute(sql)

    async def change_address_ex(self, telegram_id: int, addr: str) -> bool:
        data = await self.get_by_params(telegram_id=telegram_id)
        if data:
            user = data[0]
            if user.address != addr:
                await self.edit_by_telegram_id(telegram_id=telegram_id, address=addr)
                return True
        return False

    async def get_top(self) -> list:
        sql = select(self.model).order_by(User.win.desc()).limit(10)
        data = await self.session.execute(sql)
        return list(data.scalars().all())
