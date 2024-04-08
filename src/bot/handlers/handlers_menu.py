import hashlib
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from aiogram.utils.exceptions import MessageNotModified
from sqlalchemy.ext.asyncio import AsyncSession

from settings import settings
from src.bot.factories import dp, bot, logger, _
from src.storage.dao.nfts_dao import NftDAO
from src.storage.dao.users_dao import UserDAO
from src.storage.models import Nft
from src.storage.schemas import UserModel
from src.utils.antiflood import anti_flood


async def main_menu() -> InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    li = InlineKeyboardButton(text=_("Мои Герои"), callback_data="wallet")
    bt = InlineKeyboardButton(text=_("Добавить NFT"), callback_data="select_nft")
    top = InlineKeyboardButton(text=_("ТОП"), callback_data="top")
    game = InlineKeyboardButton(text=_("Игра"), callback_data="Search")
    keyboard.add(li, bt, top, game)
    return keyboard


async def ping(message: types.Message):
    await message.answer(_("Pong"))


@dp.callback_query_handler(lambda c: c.message.content_type == "text", text="main")
async def main(call: types.CallbackQuery):
    keyboard = await main_menu()
    try:
        await call.message.edit_text(_("Главное меню:"), reply_markup=keyboard)
    except MessageNotModified:
        pass


@dp.callback_query_handler(lambda c: c.message.content_type != "text", text="main")
async def main(call: types.CallbackQuery):
    keyboard = await main_menu()
    await bot.send_message(
        chat_id=call.message.chat.id, text=_("Главное меню:"), reply_markup=keyboard
    )
    await bot.delete_message(
        chat_id=call.from_user.id, message_id=call.message.message_id
    )


@dp.throttled(anti_flood, rate=3)
async def start(message: types.Message, db_session: AsyncSession, language: str):
    user_dao = UserDAO(session=db_session)
    nft_dao = NftDAO(session=db_session)

    if message.chat.type == "private":
        logger.info(
            f"start | User {message.from_user.first_name}:{message.from_user.id} is welcome"
        )

        user_data = await user_dao.get_by_params(telegram_id=message.from_user.id)
        if message.get_args() and user_data:
            user = user_data[0]
            opponent_nft_id = message.get_args()
            nfts = await nft_dao.get_by_params(user_id=user.id, activated=True)
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for nft in nfts:
                button = InlineKeyboardButton(
                    text=f"{nft.name_nft}",
                    callback_data=f"fight_{nft.id}:{opponent_nft_id}",
                )
                keyboard.add(button)
            kb_main = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
            keyboard.add(kb_main)
            await bot.send_message(
                chat_id=message.chat.id,
                text=_("Выберите NFT для игры"),
                reply_markup=keyboard,
            )
        else:
            if not user_data:
                user_model = UserModel(
                    telegram_id=message.from_user.id, name=message.from_user.first_name
                )
                await user_dao.add(data=user_model.model_dump())
                await db_session.commit()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            kb_wallet = InlineKeyboardButton(
                text=_("Подключить кошелёк"), callback_data="choose_wallet"
            )
            kb_main_menu = InlineKeyboardButton(text=_("Меню"), callback_data="main")
            new_lang = "ru" if language == "en" else "en"
            kb_lang = InlineKeyboardButton(
                text=_("Сменить язык") + f" [{new_lang.upper()}]", callback_data="lang"
            )
            keyboard.add(kb_wallet, kb_main_menu, kb_lang)
            await bot.send_animation(
                chat_id=message.chat.id,
                animation=open(f"images/ah.mp4", "rb"),
                caption=_(
                    "Приветствуем в боте коллекции "
                    "<a href='https://getgems.io/collection/{MAIN_COLLECTION_ADDRESS}'>TON ANTIHERO!</a>\n"
                    "Наш <a href='https://t.me/TON_ANTIHERO_NFT'>ТЕЛЕГРАМ КАНАЛ☢️</a>\n"
                ).format(MAIN_COLLECTION_ADDRESS=settings.MAIN_COLLECTION_ADDRESS),
                reply_markup=keyboard,
            )
    await bot.delete_message(
        chat_id=message.from_user.id, message_id=message.message_id
    )


def nft_status(nft: Nft):
    if nft.withdraw:
        return _("ожидает вывода из игры 📩")
    if not nft.activated:
        return _("не активирована ❌")
    if nft.duel:
        return _("в битве ⚔")
    if nft.arena:
        return _("ожидает соперника на арене 🛡")
    if nft.activated:
        return _("активирована ✅")
    else:
        return _("в обработке...")


@dp.throttled(anti_flood, rate=3)
async def wallet(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main_menu = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    kb_arena = InlineKeyboardButton(text=_("NFT на арене"), callback_data="nft_arena")
    kb_withdraw = InlineKeyboardButton(
        text=_("Активировать NFT"), callback_data="activate_nft"
    )
    kb_pay_fee = InlineKeyboardButton(
        text=_("Вывести NFT"), callback_data="nft_withdrawable"
    )
    keyboard.add(kb_arena, kb_withdraw, kb_pay_fee, kb_main_menu)
    text_address = _("Адрес кошелька: <code>{user_address}</code>\n\n").format(
        user_address=user.address
    )
    text_nft = _("Ваши герои:\n{}")
    await call.message.edit_text(
        text_address
        + text_nft.format(
            "".join(
                [
                    "\n"
                    + str(
                        "Имя: %s\nАдрес: %s\nУровень: %d\nСтатус: %s\n"
                        % (
                            nft.name_nft,
                            f"<code>{nft.address}</code>",
                            nft.rare,
                            nft_status(nft),
                        )
                    )
                    for nft in nft_data
                ]
            )
        ),
        reply_markup=keyboard,
    )


@dp.throttled(anti_flood, rate=3)
async def search(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_search_game = InlineKeyboardButton(
        text=_("Поиск игры"), callback_data="search_game"
    )
    kb_invite = InlineKeyboardButton(
        text=_("Пригласить на бой"), callback_data="invite"
    )
    kb_main = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_invite, kb_search_game, kb_main)
    await call.message.edit_text(_("Выберите игру"), reply_markup=keyboard)


@dp.throttled(anti_flood, rate=3)
async def top_callback(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main)

    top = await user_dao.get_top()
    if not top:
        top = []
    await call.message.edit_text(
        _("Топ пользователей:{}").format(
            "".join(
                ["\n" + str(f"<b>%s</b> %s" % (user.name, user.win)) for user in top]
            )
        ),
        reply_markup=keyboard,
    )


@dp.throttled(anti_flood, rate=3)
async def lang_callback(
    call: types.CallbackQuery, db_session: AsyncSession, language: str
):
    user_dao = UserDAO(session=db_session)
    new_lang = "ru" if language == "en" else "en"
    await user_dao.edit_by_telegram_id(telegram_id=call.from_user.id, language=new_lang)
    await db_session.commit()
    await call.message.answer(_("язык установлен {new_lang}").format(new_lang=new_lang.upper()))


async def inline_handler(query: types.InlineQuery, db_session: AsyncSession):
    nft_dao = NftDAO(session=db_session)

    nft_id = int(query.query)
    nft_data = await nft_dao.get_by_params(id=nft_id)
    nft = nft_data[0]

    await nft_dao.edit_by_address(address=nft.address, arena=True)
    await db_session.commit()

    result_id: str = hashlib.md5(nft.address.encode()).hexdigest()

    text = _(
        "<a href='{TELEGRAM_BOT_URL}'>TON ANTIHERO☢️</a>\n"
        "Сразись с моим {name_nft} [LVL {rare}]\nНА АРЕНЕ"
    ).format(
        TELEGRAM_BOT_URL=settings.TELEGRAM_BOT_URL, name_nft=nft.name_nft, rare=nft.rare
    )
    title = _("Пригласить на бой")
    description = _("Пригласи друга в бой")

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_fight = InlineKeyboardButton(
        text=_("Сразиться"), url=f"{settings.TELEGRAM_BOT_URL}?start={nft.id}"
    )
    keyboard.add(kb_fight)
    articles = [
        types.InlineQueryResultArticle(
            id=result_id,
            title=title,
            description=description,
            input_message_content=types.InputTextMessageContent(
                message_text=text, parse_mode=ParseMode.HTML
            ),
            reply_markup=keyboard,
        )
    ]
    await query.answer(articles, cache_time=2, is_personal=True)
    logger.info(
        f"inline_handler | User {nft.user.name}:{nft.user.telegram_id} set his {nft.name_nft}:{nft.address} on arena"
    )
