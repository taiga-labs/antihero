from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from storage.dao.base import BaseDAO
from storage.models import User


class UserDAO(BaseDAO):
    def __init__(self, session: AsyncSession, model=User):
        super().__init__(model, session)

    async def is_exists(self, user_id) -> bool:
        data = await self.get_by_params(user_id=user_id)
        if data:
            return True
        return False

    async def edit_by_user_id(self, user_id: int, **params) -> None:
        sql = update(self.model).where(self.model.user_id == user_id).values(**params)
        await self.session.execute(sql)
