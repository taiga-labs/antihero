from typing import Any

import requests
from aiogram.types import InlineKeyboardButton
from pytonapi import AsyncTonapi

from config.settings import settings


async def transaction_exist(compare_content: str) -> bool:
    tonapi = AsyncTonapi(api_key=settings.TON_API_KEY)

    search = await tonapi.blockchain.get_account_transactions(account_id=settings.MAIN_WALLET_ADDRESS,
                                                              limit=100)
    for transaction in search.transactions:
        if transaction.in_msg.decoded_body:
            text = transaction.in_msg.decoded_body.get('text', None)
            if str(text) == str(compare_content):
                return True
        pass
    return False


async def count_nfts(address: str) -> int:
    tonapi = AsyncTonapi(api_key=settings.TON_API_KEY)
    search = await tonapi.accounts.get_nfts(account_id=address,
                                            collection=settings.MAIN_COLLECTION_ADDRESS)
    count = len(search.nft_items)
    return count


async def get_nft_by_account(address: str) -> list[InlineKeyboardButton]:
    tonapi = AsyncTonapi(api_key=settings.TON_API_KEY)
    search = await tonapi.accounts.get_nfts(account_id=address,
                                            collection=settings.MAIN_COLLECTION_ADDRESS,
                                            limit=200,
                                            offset=0)
    buttons = []
    for nft in search.nft_items:
        name = nft.metadata.get('name')
        button = InlineKeyboardButton(text=f"{name}",
                                      callback_data=f"{name}")
        buttons.append(button)
    return buttons


async def search_nft_by_name(name: str, address: str, user_id: str) -> str:
    tonapi = AsyncTonapi(api_key=settings.TON_API_KEY)
    search = await tonapi.accounts.get_nfts(account_id=address,
                                            collection=settings.MAIN_COLLECTION_ADDRESS,
                                            limit=200,
                                            offset=0)
    for nft in search.nft_items:
        a = nft.metadata.get('name')
        if a == name:
            nft_address = nft.address.to_userfriendly()
            url = nft.metadata.get('image')
            filename = f"images/{user_id}.png"
            r = requests.get(url, allow_redirects=True)
            with open(filename, 'wb') as f:
                f.write(r.content)
            return nft_address


async def search_nft(nft_address: str) -> tuple[Any | None, Any] | None:
    tonapi = AsyncTonapi(api_key=settings.TON_API_KEY)
    search = await tonapi.accounts.get_nfts(account_id=settings.MAIN_WALLET_ADDRESS,
                                            collection=settings.MAIN_COLLECTION_ADDRESS,
                                            limit=200,
                                            offset=0)
    for nft in search.nft_items:
        if nft_address == nft.address.to_userfriendly():
            a = nft.metadata.get('attributes')
            rare = a[0].get('value')
            name = nft.metadata.get('name')
            return name, rare
    return None
