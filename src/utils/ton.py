import requests
from pytonapi import AsyncTonapi
from pytonapi.schema.nft import NftItem

from settings import settings


async def get_nft_by_account(address: str) -> list[NftItem]:
    tonapi = AsyncTonapi(api_key=settings.TON_API_KEY.get_secret_value())
    search = await tonapi.accounts.get_nfts(account_id=address,
                                            collection=settings.MAIN_COLLECTION_ADDRESS,
                                            limit=200,
                                            offset=0)
    return search.nft_items


async def fetch_nft_by_address(nft_address: str) -> tuple[str | None, int]:
    tonapi = AsyncTonapi(api_key=settings.TON_API_KEY.get_secret_value())
    nft = await tonapi.nft.get_item_by_address(account_id=nft_address)
    name = nft.metadata.get('name', None)
    rare = nft.metadata.get('attributes')[0].get('value', None)
    url = nft.metadata.get('image', None)
    if (name is None
            or rare is None
            or url is None):
        raise ValueError

    r = requests.get(url, allow_redirects=True)
    with open(f"images/{nft_address}.png", 'wb') as f:
        f.write(r.content)
    return name, int(rare)
