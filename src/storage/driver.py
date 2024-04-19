from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import aioredis
from aioredis import Redis

from src.storage import db_engine


def create_pool():
    return async_sessionmaker(db_engine,
                              class_=AsyncSession,
                              expire_on_commit=False)


async def get_redis_async_client(url: str) -> Redis:
    return aioredis.from_url(url=url, decode_responses=True, max_connections=32)
