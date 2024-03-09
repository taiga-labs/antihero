from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware, LifetimeControllerMiddleware
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.storage.driver import get_redis_async_client
from src.utils.wallet import get_connector


async def anti_flood(*args, **kwargs):
    m = args[0]
    await m.answer("Не так быстро")


class WalletNotConnectedMiddleware(BaseMiddleware):
    SKIP_ROUTERS = ['choose_wallet', 'connect:']

    async def on_process_callback_query(self, call: CallbackQuery, data: dict):
        if any(sr in call.data for sr in self.SKIP_ROUTERS):
            return
        redis = await get_redis_async_client()
        connector = await get_connector(chat_id=call.message.chat.id, broker=redis)
        connected = await connector.restore_connection()
        if not connected:
            await call.answer("Требуется аутентификация кошелька!\n"
                              "/start - пройти аутентификацию",
                              show_alert=True)
            await redis.close()
            raise CancelHandler
        connector.pause_connection()
        await redis.close()


class DbSessionMiddleware(LifetimeControllerMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def pre_process(self, obj, data, *args):
        async with self.session_pool() as session:
            data["db_session"] = session

    async def post_process(self, obj, data, *args):
        await data['db_session'].close()


class RedisSessionMiddleware(LifetimeControllerMiddleware):
    def __init__(self):
        super().__init__()

    async def pre_process(self, obj, data, *args):
        data["redis_session"] = await get_redis_async_client()

    async def post_process(self, obj, data, *args):
        await data["redis_session"].close()
