import json
import time
import uuid

from aiogram import types
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aioredis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.factories import dp, logger, bot
from src.bot.handlers.handlers_menu import main_menu
from src.storage.dao.games_dao import GameDAO
from src.storage.dao.nfts_dao import NftDAO
from src.storage.dao.players_dao import PlayerDAO
from src.storage.dao.users_dao import UserDAO
from src.storage.schemas import GameModel, PlayerModel, PlayerState, GameState
from src.utils.middleware import anti_flood
from settings import settings


async def invite(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(
        user_id=user.id, arena=False, duel=False, withdraw=False, activated=True
    )
    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(
            text=f"{nft.name_nft}", callback_data=f"arena_{nft.id}"
        )
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text(
        "Выберите свободные NFT для арены", reply_markup=keyboard
    )


@dp.throttled(anti_flood)
async def arena_yes(call: types.CallbackQuery):
    nft_id = call.data[6:]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_invite = InlineKeyboardButton(
        text="Пригласить на бой", switch_inline_query=f"{nft_id}"
    )
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_invite, kb_main_menu)
    await call.message.edit_text("Пригласите противника", reply_markup=keyboard)


async def search_game(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(
        user_id=user.id, arena=False, duel=False, withdraw=False, activated=True
    )

    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(
            text=f"{nft.name_nft}", callback_data=f"nft_{nft.id}"
        )
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    await call.message.edit_text("Выберите NFT для игры", reply_markup=keyboard)


@dp.throttled(anti_flood)
async def duel_yes(
    call: types.CallbackQuery, db_session: AsyncSession, game_redis_session: Redis
):
    user_dao = UserDAO(session=db_session)
    player_dao = PlayerDAO(session=db_session)
    game_dao = GameDAO(session=db_session)

    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    nft_id = int(call.data[4:])
    nft_dao = NftDAO(session=db_session)
    await nft_dao.edit_by_id(id=nft_id, duel=True)
    await db_session.commit()
    nft_data = await nft_dao.get_by_params(id=nft_id)
    nft = nft_data[0]
    logger.info(
        f"duel_yes | User {call.from_user.first_name}:{call.from_user.id} search game with nft {nft.name_nft}:{nft.address}"
    )

    nft_opponent = await nft_dao.get_opponent(user_id=user.id)
    if nft_opponent:
        logger.info(
            f"duel_yes | {nft.user.name}:{nft.user.telegram_id}:{nft.address} vs {nft_opponent.user.name}{nft_opponent.user.telegram_id}:{nft_opponent.address}"
        )

        player_id = await player_dao.add(PlayerModel(nft_id=nft.id).model_dump())
        player_opponent_id = await player_dao.add(
            PlayerModel(nft_id=nft_opponent.id).model_dump()
        )

        game_uuid = str(uuid.uuid4())
        game_model = GameModel(
            uuid=game_uuid,
            player_l_id=player_id,
            player_r_id=player_opponent_id,
            start_time=int(time.time()),
        )
        await game_dao.add(data=game_model.model_dump())
        await db_session.commit()

        player_l_state = PlayerState(player_id=player_id)
        player_r_state = PlayerState(player_id=player_opponent_id)
        game_state = GameState(
            player_l=player_l_state,
            player_r=player_r_state,
            start_time=int(time.time()),
        )
        await game_redis_session.set(
            name=game_uuid, value=json.dumps(game_state.model_dump())
        )

        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_webapp = InlineKeyboardButton(
            text="ИГРАТЬ",
            web_app=WebAppInfo(
                url=f"https://{settings.MINIAPP_HOST}/{settings.MINIAPP_PATH}?"
                f"uuid={game_uuid}&"
                f"player_id={player_id}"
            ),
        )
        keyboard.add(kb_webapp)
        await bot.send_message(
            chat_id=nft.user.telegram_id,
            text=f"Твой соперник: {nft_opponent.user.name}'s {nft_opponent.name_nft} [LVL {nft_opponent.rare}]\n\n"
            f"Игра будет активна в течение 24 часов\n"
            f"     😈ОБРАТНОГО ПУТИ НЕТ😈",
            reply_markup=keyboard,
        )

        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_webapp = InlineKeyboardButton(
            text="ИГРАТЬ",
            web_app=WebAppInfo(
                url=f"https://{settings.MINIAPP_HOST}/{settings.MINIAPP_PATH}?"
                f"uuid={game_uuid}&"
                f"player_id={player_opponent_id}"
            ),
        )
        keyboard.add(kb_webapp)
        await bot.send_message(
            chat_id=nft_opponent.user.telegram_id,
            text=f"Твой соперник: {nft.user.name}'s {nft.name_nft} [LVL {nft.rare}]\n\n"
            f"Игра будет активна в течение 24 часов\n"
            f"     😈ОБРАТНОГО ПУТИ НЕТ😈",
            reply_markup=keyboard,
        )
    else:
        logger.info(
            f"duel_yes | User {call.from_user.first_name}:{call.from_user.id} waiting for opponent"
        )
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Выйти", callback_data=f"exit_{nft_id}")
        keyboard.add(kb_main)
        await call.message.edit_text("Начинаю поиск", reply_markup=keyboard)


@dp.throttled(anti_flood)
async def fight_yes(
    call: types.CallbackQuery, db_session: AsyncSession, game_redis_session: Redis
):
    nft_dao = NftDAO(session=db_session)
    player_dao = PlayerDAO(session=db_session)
    game_dao = GameDAO(session=db_session)

    ids = call.data[6:]
    split_ids = ids.split(":")
    nft_id = int(split_ids[0])
    opponent_nft_id = int(split_ids[1])

    nft_data = await nft_dao.get_by_params(id=nft_id)
    nft = nft_data[0]

    nft_data = await nft_dao.get_by_params(id=opponent_nft_id)
    if not nft_data:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
        keyboard.add(kb_main)
        await call.message.edit_text(
            text="Ты не успел! Истек срок приглашения", reply_markup=keyboard
        )
        return
    nft_opponent = nft_data[0]
    if not nft_opponent.arena:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
        keyboard.add(kb_main)
        await call.message.edit_text(
            text="Ты не успел! Соперник снял героя с арены", reply_markup=keyboard
        )
        return
    if nft_opponent.duel:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
        keyboard.add(kb_main)
        await call.message.edit_text(
            text="Ты не успел! Соперник уже в бою", reply_markup=keyboard
        )
        return
    if nft_opponent.user.id == nft.user.id:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
        keyboard.add(kb_main)
        await call.message.edit_text(
            text="Нельзя сражаться с самим собой!", reply_markup=keyboard
        )
        return

    await nft_dao.edit_by_address(address=nft.address, arena=True, duel=True)
    await nft_dao.edit_by_address(address=nft_opponent.address, duel=True)
    await db_session.commit()

    logger.info(
        f"fight_yes | User {call.from_user.first_name}:{call.from_user.id} accept fight from {nft_opponent.user.name}:{nft_opponent.user.telegram_id}"
    )
    logger.info(
        f"fight_yes | User {call.from_user.first_name}:{call.from_user.id} choose {nft.name_nft}:{nft.address}"
    )

    player_id = await player_dao.add(PlayerModel(nft_id=nft.id).model_dump())
    player_opponent_id = await player_dao.add(
        PlayerModel(nft_id=nft_opponent.id).model_dump()
    )

    game_uuid = str(uuid.uuid4())
    game_model = GameModel(
        uuid=game_uuid,
        player_l_id=player_id,
        player_r_id=player_opponent_id,
        start_time=int(time.time()),
    )
    await game_dao.add(data=game_model.model_dump())
    await db_session.commit()

    player_l_state = PlayerState(player_id=player_id)
    player_r_state = PlayerState(player_id=player_opponent_id)
    game_state = GameState(
        player_l=player_l_state,
        player_r=player_r_state,
        start_time=int(time.time()),
    )
    await game_redis_session.set(
        name=game_uuid, value=json.dumps(game_state.model_dump())
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_webapp = InlineKeyboardButton(
        text="ИГРАТЬ",
        web_app=WebAppInfo(
            url=f"https://{settings.MINIAPP_HOST}/{settings.MINIAPP_PATH}?"
            f"uuid={game_uuid}&"
            f"player_id={player_id}"
        ),
    )
    keyboard.add(kb_webapp)
    await bot.send_message(
        chat_id=nft.user.telegram_id,
        text=f"Твой соперник: {nft_opponent.user.name}'s {nft_opponent.name_nft} [LVL {nft_opponent.rare}]\n\n"
        f"Игра будет активна в течение 15 минут\n"
        f"     😈ОБРАТНОГО ПУТИ НЕТ😈",
        reply_markup=keyboard,
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_webapp = InlineKeyboardButton(
        text="ИГРАТЬ",
        web_app=WebAppInfo(
            url=f"https://{settings.MINIAPP_HOST}/{settings.MINIAPP_PATH}?"
            f"uuid={game_uuid}&"
            f"player_id={player_opponent_id}"
        ),
    )
    keyboard.add(kb_webapp)
    await bot.send_message(
        chat_id=nft_opponent.user.telegram_id,
        text=f"Твой соперник: {nft.user.name}'s {nft.name_nft} [LVL {nft.rare}]\n\n"
        f"Игра будет активна в течение 15 минут\n"
        f"     😈ОБРАТНОГО ПУТИ НЕТ😈",
        reply_markup=keyboard,
    )


async def exit_game(call: types.CallbackQuery, db_session: AsyncSession):
    nft_id = int(call.data[5:])
    nft_dao = NftDAO(session=db_session)
    await nft_dao.edit_by_id(id=nft_id, duel=False)
    await db_session.commit()
    logger.info(
        f"exit_game | User {call.from_user.first_name}:{call.from_user.id} exit game"
    )
    keyboard = await main_menu()
    await call.message.edit_text("Главное меню:", reply_markup=keyboard)
