import hashlib
import time
from base64 import urlsafe_b64encode

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from tonsdk.boc import begin_cell
from tonsdk.utils import to_nano
from TonTools import *

from config.settings import settings
from create_bot import dp, bot
from storage.dao.nfts_dao import NftDAO
from storage.dao.users_dao import UserDAO
from storage.driver import async_session
from storage.schemas import UserModel, NftModel
from utils.game import anti_flood, UserState, determine_winner, game_winner_determined, game_draw
from utils.ton import transaction_exist, count_nfts, get_nft_by_account, search_nft_by_name, \
    search_nft
from utils.wallet import get_connector


async def main_menu() -> InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    li = InlineKeyboardButton(text="Кошелёк", callback_data="wallet")
    bt = InlineKeyboardButton(text="Добавить NFT", callback_data="add_nft")
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
    nft_dao = NftDAO(session=db_session)
    user_dao = UserDAO(session=db_session)

    if message.chat.type == 'private':
        if len(message.get_args()) > 0:
            opponent_id = message.get_args()

            # Перешедший по ссылке
            nfts = await nft_dao.get_by_params(user_id=message.from_user.id)

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

        if not await user_dao.is_exists(telegram_id=message.from_user.id):
            user_model = UserModel(telegram_id=message.from_user.id,
                                   name=message.from_user.first_name)
            await user_dao.add(data=user_model.model_dump())
            await db_session.commit()

        user_data = await user_dao.get_by_params(telegram_id=message.from_user.id)
        user = user_data[0]

        if user.verif:
            keyboard = await main_menu()
            await message.reply("Главное меню:", reply_markup=keyboard)
        if user.verif:  # TODO else
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


async def choose_wallet(call: types.CallbackQuery):
    connector = await get_connector(chat_id=call.message.chat.id)
    wallets_list = connector.get_wallets()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for w in wallets_list:
        walet_button = InlineKeyboardButton(text=w['name'], callback_data=f'connect:{w["name"]}')
        keyboard.add(walet_button)
    await call.message.answer(text='Выбери кошелек для авторизации\n\n<i>Для отмены напиши</i>"<code>Отмена</code>"',
                              parse_mode=ParseMode.HTML,
                              reply_markup=keyboard)  # TODO fix отмена


async def connect_wallet(call: types.CallbackQuery):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    connector = await get_connector(chat_id=call.message.chat.id)
    wallets_list = connector.get_wallets()
    wallet_name = call.data[8:]
    wlt = None

    for w in wallets_list:
        if w['name'] == wallet_name:
            wlt = w
            break
    if wlt is None:
        raise Exception(f'Unknown wallet: {wlt}')

    generated_url = await connector.connect(wlt)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    url_button = InlineKeyboardButton(text='Подключить', url=generated_url)
    keyboard.add(url_button)
    await call.message.answer(text='У тебя есть 3 минуты на подключение кошелька',
                              reply_markup=keyboard)

    for i in range(1, 180):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                wallet_address = connector.account.address
                wallet_address = Address(wallet_address).to_string(is_user_friendly=True, is_bounceable=False)
                await user_dao.edit_by_telegram_id(telegram_id=call.from_user.id, address=wallet_address)
                await db_session.commit()
                await call.message.answer(f'Успешная авторизация!\nАдрес кошелька:\n\n<code>{wallet_address}</code>',
                                          parse_mode=ParseMode.HTML)
                keyboard = await main_menu()
                await call.message.answer("Главное меню:", reply_markup=keyboard)

                # logger.info(f'Connected with address: {wallet_address}')  # TODO logger
            return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_retry = InlineKeyboardButton(text="Повторить", callback_data="choose_wallet")
    keyboard.add(kb_retry)
    await call.message.answer(f'Истекло время авторизации',
                              parse_mode=ParseMode.HTML,
                              reply_markup=keyboard)


async def add_nft(call: types.CallbackQuery):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    buttons = await get_nft_by_account(user.address)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.answer("Выбери свою NFT, которую хочешь добавить", reply_markup=keyboard)
    await UserState.nft.set()
    await db_session.close()


async def select_nft(call: types.CallbackQuery, state: FSMContext):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)
    if call.data == "main":
        keyboard = await main_menu()
        await call.message.edit_text("Главное меню:", reply_markup=keyboard)
        await state.finish()
    else:
        connector = await get_connector(chat_id=call.message.chat.id)
        connected = await connector.restore_connection()
        if not connected:
            await call.message.answer('Connect wallet first!')
            return

        user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
        user = user_data[0]
        nft_address = await search_nft_by_name(name=call.data, address=user.address, user_id=call.from_user.id)

        body = bytes_to_b64str(NFTItem().create_transfer_body(new_owner_address=Address(settings.MAIN_WALLET_ADDRESS),
                                                              response_address=Address(
                                                                  user.address)).to_boc())  # forward_amount=100000000
        body = body.replace("+", '-').replace("/", '_')

        transaction = {
            'valid_until': int(time.time() + 3600),
            'messages': [
                {
                    'address': nft_address,
                    'amount': to_nano(0.05, 'ton'),
                    'payload': body
                }
            ]
        }

        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_nft_prov = InlineKeyboardButton(text="Проверка перевода", callback_data=f"nft_prov_{nft_address}")
        keyboard.add(kb_nft_prov)
        await connector.send_transaction(transaction=transaction)
        await call.message.answer(text='Подтвердите перевод в приложении своего кошелька и пройдите проверку перевода',
                                  parse_mode=ParseMode.HTML)
        await state.finish()
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    await db_session.close()


@dp.throttled(anti_flood)
async def nft_transfer_prov(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    user_dao = UserDAO(session=db_session)

    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]
    nft_address = call.data[9:]
    nft_name, nft_rare = await search_nft(nft_address=nft_address)  # TODO исправить возвращаемые значения
    if nft_name:
        keyboard = await main_menu()
        kb_nft_prov = InlineKeyboardButton(text="Оплатить комиссию", callback_data=f"pay_fee_{nft_address}")
        keyboard.add(kb_nft_prov)
        await call.message.answer(
            f"Твоя NFT добавлена во внутренний кошелёк\nДля активации NFT необходимо заплатить комиссию 0.01 TON",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard)
        nft_model = NftModel(user_id=user.telegram_id,
                             address=nft_address,
                             name_nft=nft_name,
                             rare=nft_rare)
        await nft_dao.add(nft_model.model_dump())
        await db_session.commit()
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_add_nft = InlineKeyboardButton(text="Отправить", callback_data=f"add_nft")
        keyboard.add(kb_add_nft)
        await call.message.answer(f"Необходимо отправить NFT",
                                  parse_mode=ParseMode.HTML,
                                  reply_markup=keyboard)
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    await db_session.close()


async def pay_fee(call: types.CallbackQuery, state: FSMContext):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)
    if call.data == "main":
        keyboard = await main_menu()
        await call.message.edit_text("Главное меню:", reply_markup=keyboard)
        await state.finish()
    else:
        connector = await get_connector(chat_id=call.message.chat.id)
        connected = await connector.restore_connection()
        if not connected:
            await call.message.answer('Connect wallet first!')
            return

        user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
        user = user_data[0]
        nft_address = call.data[8:]

        data = {
            'address': settings.MAIN_WALLET_ADDRESS,
            'amount': str(100000000),
            'payload': urlsafe_b64encode(
                begin_cell()
                .store_uint(0, 32)
                .store_string(nft_address)
                .end_cell()
                .to_boc()
            )
            .decode()
        }

        transaction = {
            'valid_until': int(time.time() + 3600),
            'messages': [
                data
            ]
        }

        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_nft_prov = InlineKeyboardButton(text="Проверка оплаты", callback_data=f"fee_prov_{nft_address}")
        keyboard.add(kb_nft_prov)
        await connector.send_transaction(transaction=transaction)
        await call.message.answer(text='Подтвердите оплату в приложении своего кошелька и пройдите проверку перевода',
                                  parse_mode=ParseMode.HTML)
        await state.finish()
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    await db_session.close()


@dp.throttled(anti_flood)
async def fee_payment_prov(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    nft_address = call.data[9:]
    if await transaction_exist(compare_content=nft_address):
        keyboard = await main_menu()
        await call.message.answer(f"Твоя NFT добавлена во внутренний кошелёк", reply_markup=keyboard)
        await nft_dao.edit_by_address(address=nft_address, activated=True)  # TODO add activated to DB
        await db_session.commit()
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_nft_prov = InlineKeyboardButton(text="Проверка оплаты", callback_data=f"fee_prov_{nft_address}")
        kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
        keyboard.add(kb_nft_prov, kb_main_menu)
        await call.message.answer(text="Необходимо заплатить комиссию")
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    await db_session.close()


async def exit_game(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    await nft_dao.edit_by_user_id(user_id=call.from_user.id, duel=False)
    await db_session.commit()

    keyboard = await main_menu()
    await call.message.edit_text("Главное меню:", reply_markup=keyboard)
    await db_session.close()


async def wallet(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    kb_arena = InlineKeyboardButton(text="NFT на арене", callback_data="nft_arena")
    kb_pay_fee = InlineKeyboardButton(text="Активировать NFT", callback_data="activate_nft")
    keyboard.add(kb_arena, kb_pay_fee, kb_main_menu)
    text = "Ваши NFT:{}"
    await call.message.edit_text(
        text.format("".join(["\n" + str(f"Name: <b>%s</b>\nAddress: %s\nRare: %d\nActivated: %d\n" % (nft.name_nft,
                                                                                                      nft.address,
                                                                                                      nft.rare,
                                                                                                      nft.activated)) for nft in nft_data])),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard)
    await db_session.close()


async def activate_nft(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        kb_nft = InlineKeyboardButton(text=f"{nft.name_nft}",
                                      callback_data=f"pay_fee_{nft.address}")
        keyboard.add(kb_nft)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.answer("Выбери NFT, которую хочешь активировать", reply_markup=keyboard)
    await db_session.close()


async def get_nft_on_arena(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id, arena=True)

    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"remove_{nft.address}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text("Выберите NFT чтобы снять с арены", reply_markup=keyboard)
    await db_session.close()


@dp.throttled(anti_flood)
async def remove_nft_from_arena(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    address = call.data[7:]
    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id, address=address)
    nft = nft_data[0]

    await nft_dao.edit_by_address(address=address, arena=False)
    await db_session.commit()

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    await call.message.edit_text(f"NFT {nft.name_nft} снята с арены", reply_markup=keyboard)
    await db_session.close()


async def search(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_search_game = InlineKeyboardButton(text="Поиск игры", callback_data="search_game")
    kb_invite = InlineKeyboardButton(text="Пригласить на бой", callback_data="invite")
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_invite, kb_search_game, kb_main)
    await call.message.edit_text("Выберите игру", reply_markup=keyboard)


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
