import random
from aiogram import types
from aiogram.types import InlineKeyboardButton

from create_bot import bot, logger
from storage.dao.users_dao import UserDAO
from storage.dao.withdrawals_dao import WithdrawalDAO
from storage.driver import async_session
from storage.models import Nft


from storage.schemas import WithdrawModel


async def determine_winner(nft_lvl_l: int, nft_lvl_r: int) -> int:
    if nft_lvl_l - nft_lvl_r > 2:
        return 1
    if nft_lvl_r - nft_lvl_l > 2:
        return 2
    outcomes = [nft_lvl_l, nft_lvl_r, -1]
    res = random.choice(outcomes)
    if res == nft_lvl_l: return 1
    if res == nft_lvl_r: return 2
    if res == -1: return 0


async def game_winner_determined(w_nft: Nft, l_nft: Nft) -> None:
    db_session = async_session()
    user_dao = UserDAO(session=db_session)
    withdrawal_dao = WithdrawalDAO(db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    await user_dao.edit_active_by_telegram_id(telegram_id=w_nft.user.telegram_id, win=w_nft.user.win + 1)
    logger.info(f"game_winner_determined | {w_nft.user.name}'s {w_nft.name_nft} > {l_nft.user.name}'s {l_nft.name_nft}")

    vs = f"{w_nft.user.name}'s {w_nft.name_nft} ⚔️ {l_nft.user.name}'s {l_nft.name_nft}"
    await bot.send_message(chat_id=w_nft.user.telegram_id,
                           text=f"Вы выиграли!\n\nСкоро NFT придёт на ваш адрес\n\n{vs}",
                           reply_markup=keyboard)
    await bot.send_message(chat_id=l_nft.user.telegram_id,
                           text=f"Вы проиграли!\n\n{vs}",
                           reply_markup=keyboard)

    withdrawal_model = WithdrawModel(nft_address=w_nft.address,
                                     dst_address=w_nft.user.address)
    await withdrawal_dao.add(withdrawal_model.model_dump())
    logger.info(f"game_winner_determined | set withdraw pending nft:{w_nft.address} -> user:{w_nft.user.address}")

    withdrawal_model = WithdrawModel(nft_address=l_nft.address,
                                     dst_address=l_nft.user.address)
    await withdrawal_dao.add(withdrawal_model.model_dump())
    logger.info(f"game_winner_determined | set withdraw pending nft:{l_nft.address} -> user:{l_nft.user.address}")

    await db_session.commit()


async def game_draw(nft_d1: Nft, nft_d2: Nft) -> None:
    db_session = async_session()
    withdrawal_dao = WithdrawalDAO(db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    vs = f"{nft_d1.user.name}'s {nft_d1.name_nft} ⚔️ {nft_d2.user.name}'s {nft_d2.name_nft}"

    logger.info(f"game_draw | {nft_d1.user.name}'s {nft_d1.name_nft} = {nft_d2.user.name}'s {nft_d2.name_nft}")
    await bot.send_message(chat_id=nft_d1.user.telegram_id,
                           text=f"Ничья!\n\n{vs}",
                           reply_markup=keyboard)
    await bot.send_message(chat_id=nft_d2.user.telegram_id,
                           text=f"Ничья!\n\n{vs}",
                           reply_markup=keyboard)

    withdrawal_model = WithdrawModel(nft_address=nft_d1.address,
                                     dst_address=nft_d1.user.address)
    await withdrawal_dao.add(withdrawal_model.model_dump())
    logger.info(f"game_draw | set withdraw pending nft:{nft_d1.address} -> user:{nft_d1.user.address}")

    withdrawal_model = WithdrawModel(nft_address=nft_d2.address,
                                     dst_address=nft_d2.user.address)
    await withdrawal_dao.add(withdrawal_model.model_dump())
    logger.info(f"game_draw | set withdraw pending nft:{nft_d2.address} -> user:{nft_d2.user.address}")

    await db_session.commit()
