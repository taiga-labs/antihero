from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aioredis import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from settings import config
from src.storage.driver import get_redis_async_client


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["db_session"] = session
            return await handler(event, data)


class RedisMiddleware(BaseMiddleware):
    def __init__(self, redis_dsn: str):
        super().__init__()
        self.redis_dsn = redis_dsn

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        connection = await get_redis_async_client(url=self.redis_dsn)
        async with connection as conn:
            data["redis_connection"] = conn
            return await handler(event, data)
