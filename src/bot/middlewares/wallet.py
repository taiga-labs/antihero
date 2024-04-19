from typing import Callable, Dict, Any, Awaitable

from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject
from aiogram_tonconnect.tonconnect.storage.base import ATCStorageBase

from settings import settings
from src.storage.driver import get_redis_async_client
from src.utils.wallet import get_connector
from src.bot.factories import _


class WalletCheckConnectionMiddleware(BaseMiddleware):
    SKIP_ROUTERS = ["connect", "lang"]

    def __init__(
            self,
            storage: ATCStorageBase,
    ) -> None:
        self.storage = storage

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        if not data["account_wallet"]:
            await event.answer(
                _("Требуется аутентификация кошелька!\n" "/start - пройти аутентификацию"),
                show_alert=True,
            )
