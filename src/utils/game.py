from aiogram import types
from aiogram.types import InlineKeyboardButton, InputFile

from src.bot.factories import bot, logger
from src.storage.dao.nfts_dao import NftDAO
from src.storage.dao.users_dao import UserDAO
from src.storage.driver import async_session
from src.storage.models import Nft


async def game_winner_determined(w_nft: Nft, l_nft: Nft) -> None:
    db_session = async_session()
    user_dao = UserDAO(session=db_session)
    nft_dao = NftDAO(session=db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    logger.info(
        f"game_winner_determined | {w_nft.user.name}'s {w_nft.name_nft} [LVL {w_nft.rare}] > {l_nft.user.name}'s {l_nft.name_nft} [LVL {l_nft.rare}]"
    )

    await user_dao.edit_active_by_telegram_id(
        telegram_id=w_nft.user.telegram_id, win=w_nft.user.win + 1
    )
    await nft_dao.edit_by_address(
        address=w_nft.address, duel=False, arena=False, activated=False
    )
    await nft_dao.edit_by_address(
        address=l_nft.address,
        user_id=w_nft.user_id,
        duel=False,
        arena=False,
        activated=False,
    )
    await db_session.commit()

    vs = f"{w_nft.user.name}'s {w_nft.name_nft} [LVL {w_nft.rare}] ⚔️ {l_nft.user.name}'s {l_nft.name_nft} [LVL {l_nft.rare}]"

    media = types.MediaGroup()
    media.attach_photo(
        photo=InputFile(f"images/{w_nft.address}.png"),
        caption=f"🏆 Вы выиграли!\n\n{vs}\n\nНе забудьте активировать нового героя перед следующей битвой",
    )
    media.attach_photo(photo=InputFile(f"images/{l_nft.address}.png"))
    await bot.send_media_group(chat_id=w_nft.user.telegram_id, media=media)
    await bot.send_message(
        chat_id=w_nft.user.telegram_id,
        text="Вернуться в Главное меню",
        reply_markup=keyboard,
    )

    media = types.MediaGroup()
    media.attach_photo(
        photo=InputFile(f"images/{w_nft.address}.png"),
        caption=f"🫡 Вы проиграли!\n\n{vs}",
    )
    media.attach_photo(photo=InputFile(f"images/{l_nft.address}.png"))
    await bot.send_media_group(chat_id=l_nft.user.telegram_id, media=media)
    await bot.send_message(
        chat_id=l_nft.user.telegram_id,
        text="Вернуться в Главное меню",
        reply_markup=keyboard,
    )


async def game_draw(nft_d1: Nft, nft_d2: Nft) -> None:
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    logger.info(
        f"game_draw | {nft_d1.user.name}'s {nft_d1.name_nft} [LVL {nft_d1.rare}] = {nft_d2.user.name}'s {nft_d2.name_nft} [LVL {nft_d2.rare}]"
    )

    await nft_dao.edit_by_address(
        address=nft_d1.address, duel=False, arena=False, activated=False
    )
    await nft_dao.edit_by_address(
        address=nft_d2.address, duel=False, arena=False, activated=False
    )
    await db_session.commit()

    vs = f"{nft_d1.user.name}'s {nft_d1.name_nft} [LVL {nft_d1.rare}] ⚔️ {nft_d2.user.name}'s {nft_d2.name_nft} [LVL {nft_d2.rare}]"

    media = types.MediaGroup()
    media.attach_photo(
        photo=InputFile(f"images/{nft_d1.address}.png"),
        caption=f"🤝 Ничья!\n\n{vs}\n\nНе забудьте активировать героя перед следующей битвой",
    )
    media.attach_photo(photo=InputFile(f"images/{nft_d2.address}.png"))

    await bot.send_media_group(chat_id=nft_d1.user.telegram_id, media=media)
    await bot.send_message(
        chat_id=nft_d1.user.telegram_id,
        text="Вернуться в Главное меню",
        reply_markup=keyboard,
    )

    media = types.MediaGroup()
    media.attach_photo(
        photo=InputFile(f"images/{nft_d1.address}.png"),
        caption=f"🤝 Ничья!\n\n{vs}\n\nНе забудьте активировать нового героя перед следующей битвой",
    )
    media.attach_photo(photo=InputFile(f"images/{nft_d2.address}.png"))

    await bot.send_media_group(chat_id=nft_d2.user.telegram_id, media=media)
    await bot.send_message(
        chat_id=nft_d2.user.telegram_id,
        text="Вернуться в Главное меню",
        reply_markup=keyboard,
    )
