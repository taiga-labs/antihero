from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import CallbackQuery

from settings import settings
from src.storage.driver import get_redis_async_client
from src.utils.wallet import get_connector
from src.bot.factories import _


class WalletNotConnectedMiddleware(BaseMiddleware):
    SKIP_ROUTERS = ["choose_wallet", "connect:", "lang"]

    async def on_process_callback_query(self, call: CallbackQuery, data: dict):
        if any(sr in call.data for sr in self.SKIP_ROUTERS):
            return
        redis = await get_redis_async_client(url=settings.TONCONNECT_BROKER_URL)
        connector = await get_connector(chat_id=call.message.chat.id, broker=redis)
        connected = await connector.restore_connection()
        if not connected:
            await call.answer(
                _("Требуется аутентификация кошелька!\n" "/start - пройти аутентификацию"),
                show_alert=True,
            )
            await redis.close()
            raise CancelHandler
        connector.pause_connection()
        await redis.close()
