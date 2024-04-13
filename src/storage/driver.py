from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import aioredis
from aioredis import Redis

from settings import settings

db_engine = create_async_engine(
    str(settings.DATABASE_URL),
    # echo=True
)

async_session = async_sessionmaker(
    db_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_redis_async_client(url: str) -> Redis:
    return aioredis.from_url(url=url, decode_responses=True, max_connections=32)
