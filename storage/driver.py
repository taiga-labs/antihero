from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from config.settings import settings

db_engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=True
)

async_session = async_sessionmaker(db_engine,
                                   class_=AsyncSession,
                                   expire_on_commit=False,
                                   )
