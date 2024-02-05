import asyncio
import json

from TonTools.Contracts.Wallet import Wallet
from TonTools.Providers.TonCenterClient import TonCenterClient
from sqlalchemy.ext.asyncio import AsyncSession
from tonsdk.utils import Address

from config.settings import settings
from create_bot import logger
from storage.dao.withdrawals_dao import WithdrawalDAO
from storage.driver import async_session


async def process_withdrawals():
    db_session: AsyncSession = async_session()

    try:
        withdrawal_dao = WithdrawalDAO(db_session)
        provider = TonCenterClient(key=settings.TONCENTER_API_KEY)
        wallet_mnemonics = json.loads(settings.MAIN_WALLET_MNEMONICS)
        wallet = Wallet(mnemonics=wallet_mnemonics, version='v4r2', provider=provider)
        while True:
            await asyncio.sleep(25)

            unprocessed_withdrawals = await withdrawal_dao.get_active()

            if not len(unprocessed_withdrawals):
                continue

            withdrawal = unprocessed_withdrawals[0]

            nft_owner = await provider.get_nft_owner(nft_address=withdrawal.nft_address)
            nft_owner_address = Address(nft_owner).to_string(is_user_friendly=True, is_bounceable=True)
            dst_address = Address(withdrawal.dst_address).to_string(is_user_friendly=True, is_bounceable=True)

            if nft_owner_address == dst_address:
                await withdrawal_dao.close(id=withdrawal.id)
                await db_session.commit()
                logger.info(f"process_withdrawals | successful withdrawal nft:{withdrawal.nft_address} -> user:{withdrawal.dst_address}")
                continue

            withdraw_resp = await wallet.transfer_nft(destination_address=withdrawal.dst_address,
                                                      nft_address=withdrawal.nft_address,
                                                      fee=0.015)
            if withdraw_resp == 200:
                logger.info(f"process_withdrawals | provider bid accepted:{withdrawal.nft_address} -> user:{withdrawal.dst_address}")
            else:
                logger.error(
                    f"process_withdrawals | provider bid declined:{withdrawal.nft_address} -> user:{withdrawal.dst_address} | error {withdraw_resp}")
    finally:
        await db_session.close()


if __name__ == "__main__":
    try:
        asyncio.run(process_withdrawals())
    except KeyboardInterrupt:
        exit(0)
