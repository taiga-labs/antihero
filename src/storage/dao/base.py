from typing import Any

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession


class BaseDAO:
    def __init__(self, model: Any, session: AsyncSession):
        super().__init__()
        self.session = session
        self.model = model

    async def get_all(self) -> list:
        sql = select(self.model)
        data = await self.session.execute(sql)
        return list(data.scalars().all())

    async def get_by_params(self, **params) -> list:
        sql = select(self.model).filter_by(**params)  # TODO check empty params
        data = await self.session.execute(sql)
        return list(data.scalars().all())

    async def add(self, data: dict) -> int:
        sql = insert(self.model).values(**data).returning(self.model.id)
        row = await self.session.execute(sql)
        return row.fetchone().id

    async def edit_by_id(self, id: int, **params) -> None:
        sql = update(self.model).where(self.model.id == id).values(**params)
        await self.session.execute(sql)

    async def delete_by_id(self, id: int):
        sql = delete(self.model).where(self.model.id == id)
        await self.session.execute(sql)
