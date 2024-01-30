import hashlib
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from aioredis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from create_bot import dp, bot, logger
from storage.dao.nfts_dao import NftDAO
from storage.dao.users_dao import UserDAO
from storage.schemas import UserModel
from utils.middleware import anti_flood
from utils.wallet import get_connector


async def main_menu() -> InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    li = InlineKeyboardButton(text="Мои Герои", callback_data="wallet")
    bt = InlineKeyboardButton(text="Добавить NFT", callback_data="select_nft")
    top = InlineKeyboardButton(text="ТОП", callback_data="top")
    game = InlineKeyboardButton(text="Игра", callback_data="Search")
    keyboard.add(li, bt, top, game)
    return keyboard


@dp.callback_query_handler(lambda c: c.message.content_type == "text", text='main')
async def main(call: types.CallbackQuery):
    keyboard = await main_menu()
    await call.message.edit_text("Главное меню:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.message.content_type == "photo", text='main')
async def main(call: types.CallbackQuery):
    keyboard = await main_menu()
    await bot.send_message(chat_id=call.message.chat.id,
                           text="Главное меню:",
                           reply_markup=keyboard)
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)


@dp.throttled(anti_flood, rate=10)
async def start(message: types.Message, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    nft_dao = NftDAO(session=db_session)

    if message.chat.type == 'private':
        if not await user_dao.is_exists(telegram_id=message.from_user.id):
            user_model = UserModel(telegram_id=message.from_user.id,
                                   name=message.from_user.first_name)
            await user_dao.add(data=user_model.model_dump())
            await db_session.commit()

        user_data = await user_dao.get_by_params(telegram_id=message.from_user.id, active=True)
        if user_data:
            user = user_data[0]
            if len(message.get_args()) > 0:
                opponent_nft_id = message.get_args()
                nfts = await nft_dao.get_by_params(user_id=user.id, activated=True)
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                for nft in nfts:
                    button = InlineKeyboardButton(text=f"{nft.name_nft}",
                                                  callback_data=f"fight_{nft.id}:{opponent_nft_id}")
                    keyboard.add(button)
                kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
                keyboard.add(kb_main)
                await bot.send_message(chat_id=message.chat.id,
                                       text="Выберите NFT для игры",
                                       reply_markup=keyboard)
            else:
                keyboard = await main_menu()
                await bot.send_message(chat_id=message.chat.id,
                                       text="Главное меню:",
                                       reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            kb_transfer = InlineKeyboardButton(text="Подключить кошелёк", callback_data="choose_wallet")
            keyboard.add(kb_transfer)
            await bot.send_animation(chat_id=message.chat.id,
                                     animation='CgACAgIAAxkBAAIBS2WuL2bgRduEAAHGoMzH7nZEVdG2GwACIjwAAj5zcUl-Y3Gi5gNp8zQE',
                                     caption=F"Приветствуем в боте коллекции "
                                             F"<a href='https://getgems.io/collection/{settings.MAIN_COLLECTION_ADDRESS}'>TON ANTIHERO!</a>\n"
                                             F"Наш <a href='https://t.me/TON_ANTIHERO_NFT'>ТЕЛЕГРАМ КАНАЛ☢️</a>\n"
                                             F"Для начала игры нужно пройти авторизацию через TON кошелёк",
                                     reply_markup=keyboard)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)


@dp.throttled(anti_flood, rate=3)
async def wallet(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    kb_arena = InlineKeyboardButton(text="NFT на арене", callback_data="nft_arena")
    kb_pay_fee = InlineKeyboardButton(text="Активировать NFT", callback_data="activate_nft")
    kb_disconnect = InlineKeyboardButton(text="Отвязать кошелёк", callback_data="disconnect")
    keyboard.add(kb_arena, kb_pay_fee, kb_disconnect, kb_main_menu)
    text_address = f"Адрес кошелька: <code>{user.address}</code>\n\n"
    text_nft = "Ваши NFT:\n{}"
    await call.message.edit_text(
        text_address + text_nft.format(
            "".join(["\n" + str(f"Name: %s\nAddress: %s\nLevel: %d\nActivated: %s\n" % (nft.name_nft,
                                                                                        f"<code>{nft.address}</code>",
                                                                                        nft.rare,
                                                                                        "✅" if nft.activated
                                                                                        else "❌"))
                     for nft in nft_data])),
        reply_markup=keyboard)


@dp.throttled(anti_flood, rate=3)
async def search(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_search_game = InlineKeyboardButton(text="Поиск игры", callback_data="search_game")
    kb_invite = InlineKeyboardButton(text="Пригласить на бой", callback_data="invite")
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_invite, kb_search_game, kb_main)
    await call.message.edit_text("Выберите игру", reply_markup=keyboard)


@dp.throttled(anti_flood, rate=3)
async def top_callback(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    top = await user_dao.get_top()
    if not top:
        top = []
    await call.message.edit_text(
        "Топ пользователей:{}".format("".join(["\n" + str(f"<b>%s</b> %s" % (user.name, user.win)) for user in top])),
        reply_markup=keyboard)


async def disconnect(call: types.CallbackQuery, db_session: AsyncSession, redis_session: Redis):
    user_dao = UserDAO(session=db_session)
    await user_dao.edit_active_by_telegram_id(telegram_id=call.from_user.id, active=False)
    await db_session.commit()

    connector = await get_connector(chat_id=call.message.chat.id, broker=redis_session)
    await connector.restore_connection()
    await connector.disconnect()
    await call.message.edit_text(text='Адрес отвязан\n\n/start чтобы добавить адрес')
    logger.info(f"disconnect | User {call.from_user.id} is disconnected")


async def inline_handler(query: types.InlineQuery, db_session: AsyncSession):
    nft_dao = NftDAO(session=db_session)

    nft_id = int(query.query)
    nft_data = await nft_dao.get_by_params(id=nft_id)
    nft = nft_data[0]

    await nft_dao.edit_by_address(address=nft.address, arena=True)
    await db_session.commit()

    result_id: str = hashlib.md5(nft.address.encode()).hexdigest()

    text = f"<a href='{settings.TELEGRAM_BOT_URL}'>TON ANTIHERO☢️</a>\nСразись с моим {nft.name_nft}\nНА АРЕНЕ."
    title = 'Пригласить на бой'
    description = "Пригласи друга в бой"

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_fight = InlineKeyboardButton(text="Сразиться", url=f"{settings.TELEGRAM_BOT_URL}?start={nft.id}")
    keyboard.add(kb_fight)
    articles = [types.InlineQueryResultArticle(
        id=result_id,
        title=title,
        description=description,
        input_message_content=types.InputTextMessageContent(message_text=text, parse_mode=ParseMode.HTML),
        reply_markup=keyboard
    )]
    await query.answer(articles, cache_time=2, is_personal=True)
