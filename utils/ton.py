from typing import Any

import requests
from aiogram.types import InlineKeyboardButton
from pytonapi import AsyncTonapi

from config.settings import settings


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


async def search_account_nfts_by_name(address: str, name: str, user_id: str) -> tuple[str, Any | None, Any] | None:
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
            rare = a[0].get('value')
            name = nft.metadata.get('name')
            return nft_address, name, rare
