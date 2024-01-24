import random
from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton

from config.settings import settings
from create_bot import bot
from storage.dao.users_dao import UserDAO
from storage.driver import async_session
from storage.models import Nft

from TonTools import *


async def anti_flood(*args, **kwargs):
    m = args[0]
    await m.answer("Не так быстро")


class UserState(StatesGroup):
    nft = State()
    name = State()
    description = State()


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

    vs = f"NFT:\n{w_nft.user.telegram_id} ⚔️ {l_nft.user.telegram_id}"

    # print("Выиграл NFT №1")
    await bot.send_message(chat_id=w_nft.user.telegram_id,
                           text=f"Вы выиграли!\n\nСкоро NFT придёт на ваш адрес\n\n{vs}",
                           reply_markup=keyboard)
    await bot.send_message(chat_id=l_nft.user.telegram_id,
                           text=f"Вы проиграли!\n\n{vs}",
                           reply_markup=keyboard)

    await user_dao.edit_by_telegram_id(telegram_id=w_nft.user.telegram_id, win=w_nft.user.win + 1)
    await user_dao.edit_by_telegram_id(telegram_id=l_nft.user.telegram_id, bonus=l_nft.user.bonus - 1)
    await db_session.commit()

    client = TonApiClient(settings.TON_API_KEY)
    my_wallet_mnemonics = json.loads(settings.MAIN_WALLET_MNEMONICS)
    my_wallet = Wallet(provider=client, mnemonics=my_wallet_mnemonics, version='v4r2')

    # TODO добавить в бд проверку, что nft возвращена
    # await transfer_nft(win[0], result[0])
    resp = await my_wallet.transfer_nft(destination_address=w_nft.user.address, nft_address=l_nft.address)
    # print(resp)  # 200
    await asyncio.sleep(25)
    resp = await my_wallet.transfer_nft(destination_address=w_nft.user.address, nft_address=w_nft.address)
    # print(resp)  # 200


async def game_draw(nft_d1: Nft, nft_d2: Nft):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    vs = f"NFT:\n{nft_d1.user.telegram_id} ⚔️ {nft_d2.user.telegram_id}"

    await bot.send_message(chat_id=nft_d1.user.telegram_id, text=f"Ничья!\n\n{vs}", reply_markup=keyboard)
    await bot.send_message(chat_id=nft_d2.user.telegram_id, text=f"Ничья!\n\n{vs}", reply_markup=keyboard)

    await user_dao.edit_by_telegram_id(telegram_id=nft_d1.user.telegram_id, bonus=nft_d1.user.bonus - 1)
    await user_dao.edit_by_telegram_id(telegram_id=nft_d2.user.telegram_id, bonus=nft_d2.user.bonus - 1)
    await db_session.commit()

    client = TonApiClient(settings.TON_API_KEY)
    my_wallet_mnemonics = json.loads(settings.MAIN_WALLET_MNEMONICS)
    my_wallet = Wallet(provider=client, mnemonics=my_wallet_mnemonics, version='v4r2')
    await my_wallet.transfer_nft(destination_address=nft_d1.user.address, nft_address=nft_d1.address)
    await asyncio.sleep(25)
    await my_wallet.transfer_nft(destination_address=nft_d2.user.address, nft_address=nft_d2.address)
