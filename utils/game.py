import random
from aiogram import types
from aiogram.types import InlineKeyboardButton

from config.settings import settings
from create_bot import bot
from storage.dao.users_dao import UserDAO
from storage.driver import async_session
from storage.models import Nft

from TonTools import *


async def determine_winner(chance1, chance2, bonus1, bonus2):
    if bonus1 > 0:
        user_one = chance1 + bonus1
    else:
        user_one = chance1

    if bonus2 > 0:
        user_two = chance2 + bonus2
    else:
        user_two = chance2

    maximum = user_one + user_two
    r = maximum + 25
    random_number = random.randint(0, r)

    if random_number < user_one:
        return 1
    elif random_number < user_two:
        return 2
    else:
        return 0


async def game_winner_determined(w_nft: Nft, l_nft: Nft):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    vs = f"{w_nft.user.name}'s {w_nft.name_nft} ⚔️ {l_nft.user.name}'s {l_nft.name_nft}"

    await bot.send_message(chat_id=w_nft.user.telegram_id,
                           text=f"Вы выиграли!\n\nСкоро NFT придёт на ваш адрес\n\n{vs}",
                           reply_markup=keyboard)
    await bot.send_message(chat_id=l_nft.user.telegram_id,
                           text=f"Вы проиграли!\n\n{vs}",
                           reply_markup=keyboard)

    await user_dao.edit_active_by_telegram_id(telegram_id=w_nft.user.telegram_id, win=w_nft.user.win + 1)
    await user_dao.edit_active_by_telegram_id(telegram_id=l_nft.user.telegram_id, bonus=l_nft.user.bonus - 1)
    await db_session.commit()

    provider = TonCenterClient(key=settings.TONCENTER_API_KEY)
    wallet_mnemonics = json.loads(settings.MAIN_WALLET_MNEMONICS)
    wallet = Wallet(mnemonics=wallet_mnemonics, version='v4r2', provider=provider)

    # TODO добавить в бд проверку, что nft возвращена
    await wallet.transfer_nft(destination_address=w_nft.user.address, nft_address=l_nft.address, fee=0.015)
    await asyncio.sleep(25)
    await wallet.transfer_nft(destination_address=w_nft.user.address, nft_address=w_nft.address, fee=0.015)


async def game_draw(nft_d1: Nft, nft_d2: Nft):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    vs = f"{nft_d1.user.name}'s {nft_d1.name_nft} ⚔️ {nft_d2.user.name}'s {nft_d2.name_nft}"

    await bot.send_message(chat_id=nft_d1.user.telegram_id,
                           text=f"Ничья!\n\n{vs}",
                           reply_markup=keyboard)
    await bot.send_message(chat_id=nft_d2.user.telegram_id,
                           text=f"Ничья!\n\n{vs}",
                           reply_markup=keyboard)

    await user_dao.edit_active_by_telegram_id(telegram_id=nft_d1.user.telegram_id, bonus=nft_d1.user.bonus - 1)
    await user_dao.edit_active_by_telegram_id(telegram_id=nft_d2.user.telegram_id, bonus=nft_d2.user.bonus - 1)
    await db_session.commit()

    provider = TonCenterClient(key=settings.TONCENTER_API_KEY)
    wallet_mnemonics = json.loads(settings.MAIN_WALLET_MNEMONICS)
    wallet = Wallet(mnemonics=wallet_mnemonics, version='v4r2', provider=provider)
    await wallet.transfer_nft(destination_address=nft_d1.user.address, nft_address=nft_d1.address, fee=0.015)
    await asyncio.sleep(25)
    await wallet.transfer_nft(destination_address=nft_d2.user.address, nft_address=nft_d2.address, fee=0.015)
