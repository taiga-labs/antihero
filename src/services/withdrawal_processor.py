import asyncio

from TonTools.Providers.TonCenterClient import TonCenterClient
from sqlalchemy.ext.asyncio import AsyncSession
from tonsdk.utils import Address

from settings import settings
from src.bot.factories import logger
from src.services import processor_logger
from src.storage.dao.nfts_dao import NftDAO
from src.storage.dao.withdrawals_dao import WithdrawalDAO
from src.storage.driver import async_session


async def process_withdrawals():
    db_session: AsyncSession = async_session()

    try:
        withdrawal_dao = WithdrawalDAO(db_session)
        nft_dao = NftDAO(db_session)
        provider = TonCenterClient(key=settings.TONCENTER_API_KEY.get_secret_value())
        while True:
            await asyncio.sleep(1)

            unprocessed_withdrawals = await withdrawal_dao.get_active()

            if not len(unprocessed_withdrawals):
                continue

            for withdrawal in unprocessed_withdrawals:
                try:
                    nft_owner = await provider.get_nft_owner(
                        nft_address=withdrawal.nft_address
                    )
                except Exception as ex:
                    processor_logger.error(f"process_withdrawals | failed get nft owner: {ex}")
                    continue

                nft_owner_address = (
                    Address(nft_owner.address)
                    .to_string(is_user_friendly=True, is_bounceable=True)
                    .replace("+", "-")
                    .replace("/", "_")
                )
                dst_address = (
                    Address(withdrawal.dst_address)
                    .to_string(is_user_friendly=True, is_bounceable=True)
                    .replace("+", "-")
                    .replace("/", "_")
                )

                if nft_owner_address == dst_address:
                    await withdrawal_dao.close(id=withdrawal.id)
                    await nft_dao.edit_by_address(
                        address=withdrawal.nft_address,
                        duel=False,
                        arena=False,
                        activated=False,
                        withdraw=False,
                        user_id=None,
                    )
                    await db_session.commit()
                    processor_logger.info(
                        f"process_withdrawals | successful withdrawal nft:{withdrawal.nft_address} -> user:{withdrawal.dst_address}"
                    )

                await asyncio.sleep(2)
    finally:
        processor_logger.info("process_withdrawals | close withdrawal processor")
        await db_session.close()


if __name__ == "__main__":
    try:
        processor_logger.info("Start withdrawal processor...")
        asyncio.run(process_withdrawals())
    except KeyboardInterrupt:
        exit(0)
