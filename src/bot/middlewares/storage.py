from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker

from settings import settings
from src.storage.driver import get_redis_async_client


class DbSessionMiddleware(LifetimeControllerMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def pre_process(self, obj, data, *args):
        async with self.session_pool() as session:
            data["db_session"] = session

    async def post_process(self, obj, data, *args):
        await data["db_session"].close()


class RedisSessionMiddleware(LifetimeControllerMiddleware):
    TONCONNECT_ROUTERS = ["connect:", "add_nft_", "pay_fee_"]
    GAME_ROUTERS = ["nft_", "fight_"]

    def __init__(self):
        super().__init__()

    async def pre_process(self, obj, data, *args):
        data["tonconnect_redis_session"] = await get_redis_async_client(
            url=settings.TONCONNECT_BROKER_URL
        )
        data["game_redis_session"] = await get_redis_async_client(
            url=settings.GAME_BROKER_URL
        )

    async def post_process(self, obj, data, *args):
        await data["tonconnect_redis_session"].close()
        await data["game_redis_session"].close()
