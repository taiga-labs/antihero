from aiogram import types
from aiogram.types import InlineKeyboardButton

from create_bot import dp
from handlers.handlers_menu import main_menu
from storage.dao.nfts_dao import NftDAO
from storage.dao.users_dao import UserDAO
from storage.driver import async_session
from utils.game import determine_winner, game_winner_determined, game_draw
from utils.middleware import anti_flood


async def invite(call: types.CallbackQuery):
    db_session = async_session()

    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id, activated=True, arena=False)
    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"arena_{nft.id}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text("Выберите свободные NFT для арены", reply_markup=keyboard)
    await db_session.close()


@dp.throttled(anti_flood)
async def arena_yes(call: types.CallbackQuery):
    db_session = async_session()
    nft_id = call.data[6:]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_invite = InlineKeyboardButton(text="Пригласить на бой", switch_inline_query=f"{nft_id}")
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_invite, kb_main_menu)
    await call.message.edit_text("Пригласите противника", reply_markup=keyboard)
    await db_session.close()


async def search_game(call: types.CallbackQuery):
    db_session = async_session()

    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id, activated=True, arena=False)

    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"nft_{nft.id}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    await call.message.edit_text("Выберите NFT для игры", reply_markup=keyboard)
    await db_session.close()


@dp.throttled(anti_flood)
async def nft_yes(call: types.CallbackQuery):
    db_session = async_session()

    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_id = int(call.data[4:])
    nft_dao = NftDAO(session=db_session)
    await nft_dao.edit_by_id(id=nft_id, duel=True)
    await db_session.commit()

    nft_opponent = await nft_dao.get_opponent(user_id=user.id)

    if nft_opponent:
        await nft_dao.edit_by_user_id(user_id=nft_opponent.user_id, duel=False)
        await nft_dao.edit_by_user_id(user_id=call.from_user.id, duel=False)
        await db_session.commit()

        nft_data = await nft_dao.get_by_params(id=nft_id)
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

    ids = call.data[6:]
    split_ids = ids.split(':')
    nft_id = int(split_ids[0])
    opponent_nft_id = int(split_ids[1])

    nft_data = await nft_dao.get_by_params(id=nft_id)
    nft = nft_data[0]

    nft_data = await nft_dao.get_by_params(id=opponent_nft_id)
    nft_opponent = nft_data[0]

    await nft_dao.edit_by_address(address=nft.address, arena=True)
    await db_session.commit()

    game_outcome = await determine_winner(nft_opponent.rare * 10, nft.rare * 10, nft_opponent.user.bonus,
                                          nft.user.bonus)
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
