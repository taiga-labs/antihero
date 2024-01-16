from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from config.settings import settings

db_engine = create_async_engine(
    str(settings.DATABASE_URL),
)
async_session = async_sessionmaker(db_engine,
                                   class_=AsyncSession,
                                   expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
