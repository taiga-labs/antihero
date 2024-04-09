from aiogram import types
from aiogram.types import InlineKeyboardButton, InputFile

from src.bot.factories import bot, logger
from src.storage.dao.nfts_dao import NftDAO
from src.storage.dao.users_dao import UserDAO
from src.storage.driver import async_session
from src.storage.models import Nft


LOCALES = {
    "menu": {"ru": "Главное меню", "en": "Main menu"},
    "win": {
        "ru": "🏆 Вы выиграли!\n\n"
        "{w_user_name}'s {w_name_nft} [LVL {w_rare}]: {w_score}\n"
        "{l_user_name}'s {l_name_nft} [LVL {l_rare}]: {l_score}\n\n"
        "Не забудьте активировать нового героя перед следующей битвой",
        "en": "🏆 You win!\n\n"
        "{w_user_name}'s {w_name_nft} [LVL {w_rare}]: {w_score}\n"
        "{l_user_name}'s {l_name_nft} [LVL {l_rare}]: {l_score}\n\n"
        "Don't forget to activate a new hero before the next battle",
    },
    "loose": {
        "ru": "🫡 Вы проиграли!\n\n"
        "{w_user_name}'s {w_name_nft} [LVL {w_rare}]: {w_score}\n"
        "{l_user_name}'s {l_name_nft} [LVL {l_rare}]: {l_score}",
        "en": "🫡 You loose!\n\n"
        "{w_user_name}'s {w_name_nft} [LVL {w_rare}]: {w_score}\n"
        "{l_user_name}'s {l_name_nft} [LVL {l_rare}]: {l_score}",
    },
    "draw": {
        "ru": "🤝 Ничья!\n\n"
        "{d1_user_name}'s {d1_name_nft} [LVL {d1_rare}]: {d1_score}\n"
        "{d2_user_name}'s {d2_name_nft} [LVL {d2_rare}]: {d2_score}\n\n"
        "Не забудьте активировать героя перед следующей битвой",
        "en": "🤝 Draw!\n\n"
        "{d1_user_name}'s {d1_name_nft} [LVL {d1_rare}]: {d1_score}\n"
        "{d2_user_name}'s {d2_name_nft} [LVL {d2_rare}]: {d2_score}\n\n"
        "Don't forget to activate a new hero before the next battle",
    },
    "back": {"ru": "Вернуться в Главное меню", "en": "Back to main menu"},
}


async def game_winner_determined(
    w_nft: Nft, w_score: int, l_nft: Nft, l_score: int
) -> None:
    db_session = async_session()
    user_dao = UserDAO(session=db_session)
    nft_dao = NftDAO(session=db_session)

    logger.info(
        f"game_winner_determined | {w_nft.user.name}'s {w_nft.name_nft} [LVL {w_nft.rare}]: {w_score} >"
        f" {l_nft.user.name}'s {l_nft.name_nft} [LVL {l_nft.rare}]: {l_score}"
    )

    await user_dao.edit_by_telegram_id(
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
    await db_session.refresh(l_nft.user, w_nft.user)

    w_keyboard = types.InlineKeyboardMarkup(row_width=1)
    w_kb_main = InlineKeyboardButton(
        text=LOCALES["menu"][w_nft.user.language], callback_data="main"
    )
    w_keyboard.add(w_kb_main)

    media = types.MediaGroup()
    media.attach_photo(
        photo=InputFile(f"images/{w_nft.address}.png"),
        caption=LOCALES["win"][w_nft.user.language].format(
            w_user_name=w_nft.user.name,
            w_name_nft=w_nft.name_nft,
            w_rare=w_nft.rare,
            w_score=w_score,
            l_user_name=l_nft.user.name,
            l_name_nft=l_nft.name_nft,
            l_rare=l_nft.rare,
            l_score=l_score,
        ),
    )
    media.attach_photo(photo=InputFile(f"images/{l_nft.address}.png"))
    await bot.send_media_group(chat_id=w_nft.user.telegram_id, media=media)
    await bot.send_message(
        chat_id=w_nft.user.telegram_id,
        text=LOCALES["back"][w_nft.user.language],
        reply_markup=w_keyboard,
    )

    l_keyboard = types.InlineKeyboardMarkup(row_width=1)
    l_kb_main = InlineKeyboardButton(
        text=LOCALES["menu"][l_nft.user.language], callback_data="main"
    )
    l_keyboard.add(l_kb_main)

    media = types.MediaGroup()
    media.attach_photo(
        photo=InputFile(f"images/{w_nft.address}.png"),
        caption=LOCALES["loose"][l_nft.user.language].format(
            w_user_name=w_nft.user.name,
            w_name_nft=w_nft.name_nft,
            w_rare=w_nft.rare,
            w_score=w_score,
            l_user_name=l_nft.user.name,
            l_name_nft=l_nft.name_nft,
            l_rare=l_nft.rare,
            l_score=l_score,
        ),
    )
    media.attach_photo(photo=InputFile(f"images/{l_nft.address}.png"))
    await bot.send_media_group(chat_id=l_nft.user.telegram_id, media=media)
    await bot.send_message(
        chat_id=l_nft.user.telegram_id,
        text=LOCALES["back"][l_nft.user.language],
        reply_markup=l_keyboard,
    )


async def game_draw(nft_d1: Nft, score_d1: int, nft_d2: Nft, score_d2: int) -> None:
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    logger.info(
        f"game_draw | {nft_d1.user.name}'s {nft_d1.name_nft} [LVL {nft_d1.rare}]: {score_d1} = "
        f"{nft_d2.user.name}'s {nft_d2.name_nft} [LVL {nft_d2.rare}]: {score_d2}"
    )

    await nft_dao.edit_by_address(
        address=nft_d1.address, duel=False, arena=False, activated=False
    )
    await nft_dao.edit_by_address(
        address=nft_d2.address, duel=False, arena=False, activated=False
    )
    await db_session.commit()
    await db_session.refresh(nft_d1.user, nft_d2.user)

    vs = (
        f"{nft_d1.user.name}'s {nft_d1.name_nft} [LVL {nft_d1.rare}]: {score_d1}\n"
        f"{nft_d2.user.name}'s {nft_d2.name_nft} [LVL {nft_d2.rare}]: {score_d2}"
    )

    d1_keyboard = types.InlineKeyboardMarkup(row_width=1)
    d1_kb_main = InlineKeyboardButton(
        text=LOCALES["menu"][nft_d1.user.language], callback_data="main"
    )
    d1_keyboard.add(d1_kb_main)

    media = types.MediaGroup()
    media.attach_photo(
        photo=InputFile(f"images/{nft_d1.address}.png"),
        caption=LOCALES["draw"][nft_d1.user.language].format(
            d1_user_name=nft_d1.user.name,
            d1_name_nft=nft_d1.name_nft,
            d1_rare=nft_d1.rare,
            d1_score=score_d1,
            d2_user_name=nft_d2.user.name,
            d2_name_nft=nft_d2.name_nft,
            d2_rare=nft_d2.rare,
            d2_score=score_d2,
        ),
    )
    media.attach_photo(photo=InputFile(f"images/{nft_d2.address}.png"))

    await bot.send_media_group(chat_id=nft_d1.user.telegram_id, media=media)
    await bot.send_message(
        chat_id=nft_d1.user.telegram_id,
        text=LOCALES["back"][nft_d1.user.language],
        reply_markup=d1_keyboard,
    )

    d2_keyboard = types.InlineKeyboardMarkup(row_width=1)
    d2_kb_main = InlineKeyboardButton(
        text=LOCALES["menu"][nft_d2.user.language], callback_data="main"
    )
    d2_keyboard.add(d2_kb_main)

    media = types.MediaGroup()
    media.attach_photo(
        photo=InputFile(f"images/{nft_d1.address}.png"),
        caption=LOCALES["draw"][nft_d2.user.language].format(
            d1_user_name=nft_d1.user.name,
            d1_name_nft=nft_d1.name_nft,
            d1_rare=nft_d1.rare,
            d1_score=score_d1,
            d2_user_name=nft_d2.user.name,
            d2_name_nft=nft_d2.name_nft,
            d2_rare=nft_d2.rare,
            d2_score=score_d2,
        ),
    )
    media.attach_photo(photo=InputFile(f"images/{nft_d2.address}.png"))

    await bot.send_media_group(chat_id=nft_d2.user.telegram_id, media=media)
    await bot.send_message(
        chat_id=nft_d2.user.telegram_id,
        text=LOCALES["back"][nft_d2.user.language],
        reply_markup=d2_keyboard,
    )
