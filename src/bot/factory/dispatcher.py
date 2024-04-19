from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_tonconnect.handlers import AiogramTonConnectHandlers
from aiogram_tonconnect.middleware import AiogramTonConnectMiddleware
from aiogram_tonconnect.tonconnect.storage.base import ATCRedisStorage
from aiogram_tonconnect.utils.qrcode import QRUrlProvider

from settings import config
from src.bot.handlers.test import router_test
from src.bot.middlewares.storage import DatabaseMiddleware, RedisMiddleware
from src.storage.driver import create_pool, get_redis_async_client


def _setup_outer_middlewares(dispatcher: Dispatcher) -> None:
    db_session_pool = create_pool()
    dispatcher.update.outer_middleware(DatabaseMiddleware(session_pool=db_session_pool))
    # dispatcher.update.outer_middleware(RedisMiddleware())
    # i18n = LocalizationMiddleware("antihero", "locales")
    # dispatcher.update.outer_middleware(i18n)
    # return i18n

    EXCLUDE_WALLETS = ["mytonwallet"]

    tonconnect_storage = RedisStorage.from_url(str(config.broker.TONCONNECT_REDIS_DSN))
    dispatcher.update.middleware.register(
        AiogramTonConnectMiddleware(
            storage=ATCRedisStorage(redis=tonconnect_storage.redis),
            manifest_url=config.ton.MANIFEST_URL,
            exclude_wallets=EXCLUDE_WALLETS,
            qrcode_provider=QRUrlProvider(),
        )
    )


def create_dispatcher() -> Dispatcher:
    dispatcher: Dispatcher = Dispatcher(
        name="main_dispatcher",
        storage=MemoryStorage(),  # TODO migrate to redis
    )

    _setup_outer_middlewares(dispatcher=dispatcher)
    # _ = i18n.lazy_gettext

    AiogramTonConnectHandlers().register(dispatcher)

    dispatcher.include_routers(router_test)

    return dispatcher
