import hashlib
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from config.settings import settings
from create_bot import dp, bot
from storage.dao.nfts_dao import NftDAO
from storage.dao.users_dao import UserDAO
from storage.driver import async_session, get_redis_async_client
from storage.schemas import UserModel
from utils.middleware import anti_flood
from utils.wallet import get_connector


async def main_menu() -> InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    li = InlineKeyboardButton(text="Кошелёк", callback_data="wallet")
    bt = InlineKeyboardButton(text="Добавить NFT", callback_data="select_nft")
    top = InlineKeyboardButton(text="ТОП", callback_data="top")
    game = InlineKeyboardButton(text="Игра", callback_data="Search")
    keyboard.add(li, bt, top, game)
    return keyboard


async def main(call: types.CallbackQuery):
    keyboard = await main_menu()
    await call.message.edit_text("Главное меню:", reply_markup=keyboard)


@dp.throttled(anti_flood, rate=10)
async def start(message: types.Message):
    db_session = async_session()
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
                opponent_id = message.get_args()
                nfts = await nft_dao.get_by_params(user_id=user.id)
                buttons = []
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                for nft in nfts:
                    button = InlineKeyboardButton(text=f"{nft.name_nft}",
                                                  callback_data=f"fight_{opponent_id}_{nft.address}")
                    buttons.append(button)
                keyboard.add(*buttons)
                kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
                keyboard.add(kb_main)
                await message.reply("Выберите NFT для игры", reply_markup=keyboard)
            else:
                keyboard = await main_menu()
                await message.reply("Главное меню:", reply_markup=keyboard)
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
                                     parse_mode=ParseMode.HTML,
                                     reply_markup=keyboard)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await db_session.close()


@dp.throttled(anti_flood, rate=3)
async def wallet(call: types.CallbackQuery):
    db_session = async_session()

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
    text_address = f"Адрес кошелька: {user.address}\n\n"
    text_nft = "Ваши NFT:{}"
    await call.message.edit_text(
        text_address + text_nft.format(
            "".join(["\n" + str(f"Name: <b>%s</b>\nAddress: %s\nRare: %d\nActivated: %d\n" % (nft.name_nft,
                                                                                              nft.address,
                                                                                              nft.rare,
                                                                                              nft.activated))
                     for nft in nft_data])),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard)
    await db_session.close()


@dp.throttled(anti_flood, rate=3)
async def search(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_search_game = InlineKeyboardButton(text="Поиск игры", callback_data="search_game")
    kb_invite = InlineKeyboardButton(text="Пригласить на бой", callback_data="invite")
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_invite, kb_search_game, kb_main)
    await call.message.edit_text("Выберите игру", reply_markup=keyboard)


@dp.throttled(anti_flood, rate=3)
async def top_callback(call: types.CallbackQuery):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)

    top = await user_dao.get_top()
    if not top:
        top = []
    await call.message.edit_text(
        "Топ пользователей:{}".format("".join(["\n" + str(f"<b>%s</b> %s" % (user.name, user.win)) for user in top])),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard)
    await db_session.close()


async def disconnect(call: types.CallbackQuery):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)
    await user_dao.edit_active_by_telegram_id(telegram_id=call.from_user.id, active=False)

    redis = await get_redis_async_client()
    connector = await get_connector(chat_id=call.message.chat.id, broker=redis)
    await connector.restore_connection()
    await connector.disconnect()
    await call.message.answer('Адрес отвязан')
    await redis.close()


async def inline_handler(query: types.InlineQuery):
    text = query.query or "echo"
    result_id: str = hashlib.md5(text.encode()).hexdigest()

    id = query.from_user.id

    text = f"<a href='{settings.TELEGRAM_BOT_URL}'>TON ANTIHERO☢️</a>\nСразись с моим {text}\nНА АРЕНЕ."
    title = 'Пригласить на бой'
    description = "Пригласи друга в бой"

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_fight = InlineKeyboardButton(text="Сразиться", url=f"{settings.TELEGRAM_BOT_URL}?start={id}")
    keyboard.add(kb_fight)
    articles = [types.InlineQueryResultArticle(
        id=result_id,
        title=title,
        description=description,
        input_message_content=types.InputTextMessageContent(message_text=text, parse_mode=ParseMode.HTML),
        reply_markup=keyboard
    )]

    await query.answer(articles, cache_time=2, is_personal=True)
