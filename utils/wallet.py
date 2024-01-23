from aioredis import Redis
from pytonconnect import TonConnect
from pytonconnect.storage import IStorage, DefaultStorage

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from storage.dao.users_dao import UserDAO
from storage.driver import get_redis_async_client
from storage.schemas import UserModel


class TcStorage(IStorage):
    def __init__(self, chat_id: int, broker_client: Redis):
        self.client = broker_client
        self.chat_id = chat_id

    def _get_key(self, key: str):
        return str(self.chat_id) + key

    async def set_item(self, key: str, value: str):
        await self.client.set(name=self._get_key(key), value=value)

    async def get_item(self, key: str, default_value: str = None):
        value = await self.client.get(name=self._get_key(key))
        # return value.decode() if value else default_value
        return value if value else default_value

    async def remove_item(self, key: str):
        await self.client.delete(self._get_key(key))


async def get_connector(chat_id: int):
    redis = await get_redis_async_client()
    async with redis.client() as broker:
        return TonConnect(settings.MANIFEST_URL, storage=TcStorage(chat_id=chat_id, broker_client=broker))
