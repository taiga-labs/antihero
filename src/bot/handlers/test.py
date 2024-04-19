from typing import Final

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.types import Message, User
from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import ConnectWalletCallbacks
from aioredis import Redis

from settings import config
from src.bot.middlewares.storage import RedisMiddleware

router_test: Final[Router] = Router(name=__name__)
router_test.message.outer_middleware()
router_test.message.outer_middleware(
    RedisMiddleware(redis_dsn=str(config.broker.GAME_REDIS_DSN))
)


async def a(event_from_user: User, atc_manager: ATCManager, **_):
    await atc_manager._send_message("after")
    await atc_manager.disconnect_wallet()

async def b(event_from_user: User, atc_manager: ATCManager, **_):
    await atc_manager._send_message("before")


@router_test.message(F.content_type == ContentType.TEXT)
async def ping(message: Message, atc_manager: ATCManager, redis_connection: Redis):
    callbacks = ConnectWalletCallbacks(
        before_callback=b,
        after_callback=a,
    )
    # Open the connect wallet window using the ATCManager instance
    # and the specified callbacks
    await atc_manager.connect_wallet(callbacks, check_proof=True)

    await message.answer("Pong")
