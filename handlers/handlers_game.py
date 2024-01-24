from aiogram import types
from aiogram.types import InlineKeyboardButton

from create_bot import dp
from handlers.handlers_menu import main_menu
from storage.dao.nfts_dao import NftDAO
from storage.driver import async_session
from utils.game import anti_flood, determine_winner, game_winner_determined, game_draw


async def invite(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id, activated=True)
    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"arena_{nft.address}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text("Выберите NFT для арены", reply_markup=keyboard)
    await db_session.close()


@dp.throttled(anti_flood)
async def arena_yes(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    address = call.data[6:]
    await nft_dao.edit_by_address(address=address, arena=True)
    await db_session.commit()

    nft_data = await nft_dao.get_by_params(address=address)
    nft = nft_data[0]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_invite = InlineKeyboardButton(text="Пригласить на бой", switch_inline_query=f"{nft.name_nft}")
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_invite, kb_main_menu)
    await call.message.edit_text("Пригласите противника", reply_markup=keyboard)
    await db_session.close()


async def search_game(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id, activated=True, arena=False)

    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"nft_{nft.address}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    await call.message.edit_text("Выберите NFT для игры", reply_markup=keyboard)
    await db_session.close()


@dp.throttled(anti_flood)
async def nft_yes(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    address = call.data[4:]
    await nft_dao.edit_by_address(address=address, duel=True)
    await db_session.commit()

    nft_opponent = await nft_dao.get_opponent(user_id=call.from_user.id)

    if nft_opponent:
        await nft_dao.edit_by_user_id(user_id=nft_opponent.user_id, duel=False)
        await nft_dao.edit_by_user_id(user_id=call.from_user.id, duel=False)
        await db_session.commit()

        nft_data = await nft_dao.get_by_params(address=address)
        nft = nft_data[0]

        game_outcome = determine_winner(nft_opponent.rare * 10, nft.rare * 10, nft_opponent.user.bonus, nft.user.bonus)
        if game_outcome == 1:
            await game_winner_determined(w_nft=nft_opponent, l_nft=nft)
        elif game_outcome == 2:
            await game_winner_determined(w_nft=nft, l_nft=nft_opponent)
        else:
            await game_draw(nft_d1=nft, nft_d2=nft_opponent)

        await nft_dao.delete_by_address(address=nft.address)
        await nft_dao.delete_by_address(address=nft_opponent.address)
        await db_session.commit()
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Выйти", callback_data="exit")
        keyboard.add(kb_main)
        await call.message.edit_text("Начинаю поиск", reply_markup=keyboard)
    await db_session.close()


@dp.throttled(anti_flood)
async def fight_yes(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    string = call.data
    split_result = string.split('_', 2)
    opponent_id = int(split_result[1])  # ID link
    nft_address = split_result[2]  # NFT address

    nft_data = await nft_dao.get_by_params(address=nft_address, arena=True)
    nft = nft_data[0]

    nft_data = await nft_dao.get_by_params(user_id=opponent_id, arena=True)
    nft_opponent = nft_data[0]

    await nft_dao.edit_by_user_id(user_id=nft_opponent.user.telegram_id, arena=True)
    await nft_dao.edit_by_user_id(user_id=call.from_user.id, arena=True)
    await db_session.commit()

    game_outcome = await determine_winner(nft_opponent.rare * 10, nft.rare * 10, nft_opponent.user.bonus,
                                          nft.user.bonus)
    game_outcome = 0
    if game_outcome == 1:
        await game_winner_determined(w_nft=nft_opponent, l_nft=nft)
    elif game_outcome == 2:
        await game_winner_determined(w_nft=nft, l_nft=nft_opponent)
    else:
        await game_draw(nft_d1=nft, nft_d2=nft_opponent)

    await nft_dao.delete_by_address(address=nft.address)
    await nft_dao.delete_by_address(address=nft_opponent.address)
    await db_session.commit()


async def exit_game(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    await nft_dao.edit_by_user_id(user_id=call.from_user.id, duel=False)
    await db_session.commit()

    keyboard = await main_menu()
    await call.message.edit_text("Главное меню:", reply_markup=keyboard)
    await db_session.close()
