from sqlalchemy.ext.asyncio import create_async_engine

from settings import config

db_engine = create_async_engine(
    str(config.database.POSTGRES_DSN),
    # echo=True
)
