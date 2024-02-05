from aiogram import types
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from create_bot import dp, logger
from handlers.handlers_menu import main_menu
from storage.dao.nfts_dao import NftDAO
from storage.dao.users_dao import UserDAO
from utils.game import determine_winner, game_winner_determined, game_draw
from utils.middleware import anti_flood


async def invite(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id, activated=True, arena=False, duel=False)
    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"arena_{nft.id}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text("Выберите свободные NFT для арены", reply_markup=keyboard)


@dp.throttled(anti_flood)
async def arena_yes(call: types.CallbackQuery):
    nft_id = call.data[6:]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_invite = InlineKeyboardButton(text="Пригласить на бой", switch_inline_query=f"{nft_id}")
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_invite, kb_main_menu)
    await call.message.edit_text("Пригласите противника", reply_markup=keyboard)


async def search_game(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id, activated=True, arena=False, duel=False)

    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"nft_{nft.id}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    await call.message.edit_text("Выберите NFT для игры", reply_markup=keyboard)


@dp.throttled(anti_flood)
async def nft_yes(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_id = int(call.data[4:])
    nft_dao = NftDAO(session=db_session)
    await nft_dao.edit_by_id(id=nft_id, duel=True)
    await db_session.commit()
    logger.info(f"nft_yes | User {call.from_user.id} search game")

    nft_opponent = await nft_dao.get_opponent(user_id=user.id)
    if nft_opponent:
        nft_data = await nft_dao.get_by_params(id=nft_id)
        nft = nft_data[0]

        logger.info(
            f"nft_yes | {nft.user.telegram_id}:{nft.address} vs {nft_opponent.user.telegram_id}:{nft_opponent.address}")
        game_outcome = determine_winner(nft_lvl_l=nft.rare, nft_lvl_r=nft_opponent.rare)
        if game_outcome == 1:
            await game_winner_determined(w_nft=nft, l_nft=nft_opponent)
        elif game_outcome == 2:
            await game_winner_determined(w_nft=nft_opponent, l_nft=nft)
        else:
            await game_draw(nft_d1=nft, nft_d2=nft_opponent)

        await nft_dao.delete_by_address(address=nft.address)
        await nft_dao.delete_by_address(address=nft_opponent.address)
        await db_session.commit()
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Выйти", callback_data=f"exit_{nft_id}")
        keyboard.add(kb_main)
        await call.message.edit_text("Начинаю поиск", reply_markup=keyboard)


@dp.throttled(anti_flood)
async def fight_yes(call: types.CallbackQuery, db_session: AsyncSession):
    nft_dao = NftDAO(session=db_session)

    ids = call.data[6:]
    split_ids = ids.split(':')
    nft_id = int(split_ids[0])
    opponent_nft_id = int(split_ids[1])

    nft_data = await nft_dao.get_by_params(id=nft_id)
    nft = nft_data[0]
    logger.info(f"fight_yes | User {call.from_user.id} accept fight")
    logger.info(f"fight_yes | User {call.from_user.id} choose {nft.name_nft}:{nft.address}")

    nft_data = await nft_dao.get_by_params(id=opponent_nft_id)
    if not nft_data:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
        keyboard.add(kb_main)
        await call.message.edit_text(text="Ты не успел! Истек срок приглашения",
                                     reply_markup=keyboard)
        return
    nft_opponent = nft_data[0]
    if nft_opponent.duel:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
        keyboard.add(kb_main)
        await call.message.edit_text(text="Ты не успел! Соперник уже в бою",
                                     reply_markup=keyboard)
        return
    if nft_opponent.user.id == nft.user.id:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
        keyboard.add(kb_main)
        await call.message.edit_text(text="Нельзя сражаться с самим собой!",
                                     reply_markup=keyboard)
        return

    await nft_dao.edit_by_address(address=nft.address, arena=True, duel=True)
    await nft_dao.edit_by_address(address=nft_opponent.address, duel=True)
    await db_session.commit()

    game_outcome = await determine_winner(nft_lvl_l=nft.rare, nft_lvl_r=nft_opponent.rare)
    if game_outcome == 1:
        await game_winner_determined(w_nft=nft, l_nft=nft_opponent)
    elif game_outcome == 2:
        await game_winner_determined(w_nft=nft_opponent, l_nft=nft)
    else:
        await game_draw(nft_d1=nft, nft_d2=nft_opponent)

    await nft_dao.delete_by_address(address=nft.address)
    await nft_dao.delete_by_address(address=nft_opponent.address)
    await db_session.commit()


async def exit_game(call: types.CallbackQuery, db_session: AsyncSession):
    nft_id = int(call.data[5:])
    nft_dao = NftDAO(session=db_session)
    await nft_dao.edit_by_id(id=nft_id, duel=False)
    await db_session.commit()

    keyboard = await main_menu()
    await call.message.edit_text("Главное меню:", reply_markup=keyboard)
