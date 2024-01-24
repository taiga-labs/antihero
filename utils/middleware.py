from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import CallbackQuery

from storage.driver import get_redis_async_client
from utils.wallet import get_connector


async def anti_flood(*args, **kwargs):
    m = args[0]
    await m.answer("Не так быстро")


class WalletConnectionMiddleware(BaseMiddleware):
    SKIP_ROUTERS = ['choose_wallet', 'connect:']
    async def on_process_callback_query(self, call: CallbackQuery, data: dict):
        if any(sr in call.data for sr in self.SKIP_ROUTERS):
            return
        redis = await get_redis_async_client()
        connector = await get_connector(chat_id=call.message.chat.id, broker=redis)
        connected = await connector.restore_connection()
        if not connected:
            await call.answer('Требуется аутентификация кошелька!\n'
                              '/start - пройти аутентификацию',
                              show_alert=True)
            await redis.close()
            raise CancelHandler
        await redis.close()
