import hashlib

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tonsdk.contract.token.nft import NFTItem
from tonsdk.utils import bytes_to_b64str, Address, to_nano
from TonTools import *

from config.settings import settings
from create_bot import dp, bot
from storage.dao.base import BaseDAO
from storage.dao.nfts_dao import NftDAO
from storage.dao.users_dao import UserDAO
from storage.driver import async_session
from storage.models import Nft, User
from storage.schemas import UserModel, NftModel
from utils.game import anti_flood, UserState, determine_winner, game_winner_determined, game_draw
from utils.ton import transaction_exist, count_nfts, get_nft_name, search_nft_by_name, \
    search_nft_game


async def main_menu() -> InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    li = InlineKeyboardButton(text="Кошелёк", callback_data="wallet")
    bt = InlineKeyboardButton(text="Добавить NFT", callback_data="add_nft")
    top = InlineKeyboardButton(text="ТОП", callback_data="top")
    game = InlineKeyboardButton(text="Игра", callback_data="Search")
    keyboard.add(li, bt, top, game)
    return keyboard


@dp.throttled(anti_flood, rate=10)
async def start(message: types.Message):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    user_dao = UserDAO(session=db_session)

    if message.chat.type == 'private':
        if len(message.get_args()) > 0:
            id = message.get_args()

            # Перешедший по ссылке
            nfts = await nft_dao.get_by_params(user_id=message.from_user.id)

            buttons = []
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for nft in nfts:
                button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"fight_{id}_{nft.address}")
                buttons.append(button)
            keyboard.add(*buttons)
            main = InlineKeyboardButton(text="Главное меню", callback_data="main")
            keyboard.add(main)
            await message.answer("Выберите NFT для игры", reply_markup=keyboard)

        await bot.delete_message(message.chat.id, message.message_id)

        if not await user_dao.is_exists(user_id=message.from_user.id):
            user_model = UserModel(user_id=message.from_user.id,
                                   name=message.from_user.first_name,
                                   address=message.from_user.id)
            await user_dao.add(data=user_model.model_dump())
            await db_session.commit()

        user_data = await user_dao.get_by_params(user_id=message.from_user.id)
        user = user_data[0]

        if user.user_id == message.from_user.id:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            li = InlineKeyboardButton(text="Перевод 0.01 TON", callback_data="option_one")
            keyboard.add(li)
            await bot.send_video(chat_id=message.chat.id,
                                 video='BAACAgIAAxkBAAPSZMTai_fugBIXQvUCISwMawVGrmMAAj03AALuBxhKZ4r81mDV5EAvBA',
                                 caption=F"Приветствуем в боте коллекции <a href='https://getgems.io/collection/{settings.MAIN_COLLECTION_ADDRESS}'>TON ANTIHERO!</a>\nНаш <a href='https://t.me/TON_ANTIHERO_NFT'>ТЕЛЕГРАМ КАНАЛ☢️</a>\nДля подтверждения наличия NFT нужно пройти верификацию:",
                                 reply_markup=keyboard)
        if user.verif:
            keyboard = await main_menu()
            await message.answer("Главное меню:", reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup()
            bt = InlineKeyboardButton(text="Проверка оплаты", callback_data="prov")
            keyboard.add(bt)
            await message.answer("Кажется у тебя нет NFT...", reply_markup=keyboard)


async def option_one(call: types.CallbackQuery):
    await UserState.addr.set()
    await call.message.answer('Введи свой TON кошелёк\n\n<i>Для отмены напишите</i>"<code>Отмена</code>"')


async def add_address(message: types.Message, state: FSMContext):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    await bot.delete_message(message.chat.id, message.message_id)
    if message.text.lower() == "отмена":
        await state.finish()
        await message.reply("Отменил\n\nВведите /start")
    elif message.text.startswith("E"):
        try:
            await user_dao.edit_by_user_id(user_id=message.from_user.id, address=message.text)
            await db_session.commit()
            link = f"https://app.tonkeeper.com/transfer/{settings.MAIN_WALLET_ADDRESS}?amount=10000000&text={message.from_user.id}"
            keyboard = types.InlineKeyboardMarkup()
            li = InlineKeyboardButton(text="Оплата", url=link)
            bt = InlineKeyboardButton(text="Проверка оплаты", callback_data="prov")
            keyboard.add(li, bt)
            await message.answer("Переведи 0.01 TON, чтобы я смог найти твои NFT", reply_markup=keyboard)
        except Exception as err:
            print(err)
            await bot.send_message(message.from_user.id, "Мне кажется, этот кошелёк уже есть...")
    await state.finish()


@dp.throttled(anti_flood, rate=10)
async def callback_account_payment_prove(call: types.CallbackQuery):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(user_id=call.from_user.id)
    user = user_data[0]

    if await transaction_exist(compare_tg_id=call.from_user.id):
        nfts_count = await count_nfts(address=user.address)
        if nfts_count >= 1:
            await user_dao.edit_by_user_id(user_id=call.from_user.id, count=nfts_count)
            await db_session.commit()
            keyboard = types.InlineKeyboardMarkup()
            await call.message.answer(f"У тебя {nfts_count} NFT!", reply_markup=keyboard)
            buttons = await get_nft_name(user.addr)
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(*buttons)
            await call.message.answer("Выбери свою NFT, которую хочешь поставить", reply_markup=keyboard)
            await UserState.nft.set()

            await user_dao.edit_by_user_id(user_id=call.from_user.id, verif=True, address=user.address)
            await db_session.commit()
        else:
            keyboard = types.InlineKeyboardMarkup()
            bt = InlineKeyboardButton(text="Проверка оплаты", callback_data="prov")
            keyboard.add(bt)
            await call.message.answer("Кажется у тебя нет NFT...", reply_markup=keyboard)
    else:
        await call.answer("Я не вижу твоего перевода..")


async def select_nft(call: types.CallbackQuery, state: FSMContext):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)
    if call.data == "main":
        keyboard = await main_menu()
        await call.message.edit_text("Главное меню:", reply_markup=keyboard)
        await state.finish()
    else:
        user_data = await user_dao.get_by_params(user_id=call.from_user.id)
        user = user_data[0]
        nft_address = await search_nft_by_name(name=call.data, address=user.address, user_id=call.from_user.id)

        body = bytes_to_b64str(NFTItem().create_transfer_body(new_owner_address=Address(settings.MAIN_WALLET_ADDRESS),
                                                              response_address=Address(
                                                                  user.address)).to_boc())  # forward_amount=100000000
        body = body.replace("+", '-').replace("/", '_')
        transfer_url = F"https://app.tonkeeper.com/transfer/{nft_address}?amount={to_nano(0.05, 'ton')}&bin={body}"
        link = F"https://app.tonkeeper.com/transfer/{settings.MAIN_WALLET_ADDRESS}?amount=100000000&text={nft_address}"
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        set_name = InlineKeyboardButton(text="Отправить NFT", url=transfer_url)
        set_description = InlineKeyboardButton(text="Оплата игры", url=link)
        check = InlineKeyboardButton(text="Проверка оплаты", callback_data=f"game_{nft_address}")
        keyboard.add(set_name, set_description, check)
        await bot.send_photo(call.from_user.id, photo=open(f'image/{call.from_user.id}.png', 'rb'),
                             caption=f"Чтобы сыграть необходимо отправить NFT на адрес <code>{settings.MAIN_WALLET_ADDRESS}</code> и произвести оплату в 0.1 TON",
                             reply_markup=keyboard)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await state.finish()


@dp.throttled(anti_flood)
async def callback_game_payment_prove(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = BaseDAO(model=User, session=db_session)

    nft_address = call.data[5:]
    if await transaction_exist(nft_address):
        nft_rare = search_nft_game(call.data)  # TODO исправить возвращаемые значения
        if nft_rare:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            keyboard = await main_menu()
            await call.message.answer(f"Твоя NFT добавлена во внутренний кошелёк", reply_markup=keyboard)
            nft = NftModel(user_id=call.from_user.id,
                           address=nft_address,
                           name_nft=call.data,
                           rare=nft_rare)
            await nft_dao.add(nft.model_dump())
            await db_session.commit()
        else:
            await call.answer("Необходимо отправить NFT")
    else:
        await call.answer("Необходимо заплатить комиссию")


async def main(call: types.CallbackQuery):
    keyboard = await main_menu()
    await call.message.edit_text("Главное меню:", reply_markup=keyboard)


async def exit_game(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    await nft_dao.edit_by_user_id(user_id=call.from_user.id, duel=False)
    await db_session.commit()

    keyboard = await main_menu()
    await call.message.edit_text("Главное меню:", reply_markup=keyboard)


async def add_nft(call: types.CallbackQuery):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    user_data = await user_dao.get_by_params(user_id=call.from_user.id)
    user = user_data[0]

    buttons = await get_nft_name(user.addr)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.answer("Выбери свою NFT, которую хочешь добавить", reply_markup=keyboard)
    await UserState.nft.set()


async def wallet(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    arena = InlineKeyboardButton(text="NFT на арене", callback_data="nft_arena")
    keyboard.add(arena, kb_main_menu)
    text = "Ваши NFT:{}"
    await call.message.edit_text(
        text.format("".join(["\n" + str(f"<b>%s</b> %s" % (nft.name_nft, nft.address)) for nft in nft_data])),
        reply_markup=keyboard)


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


@dp.throttled(anti_flood)
async def remove_nft_from_arena(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    address = call.data[7:]
    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id, address=address)
    nft = nft_data[0]

    await nft_dao.edit_by_address(address=address, arens=False)
    await db_session.commit()

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(main)
    await call.message.edit_text(f"NFT {nft.name_nft} снята с арены", reply_markup=keyboard)


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
    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id)
    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"arena_{nft.address}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text("Выберите NFT для арены", reply_markup=keyboard)


@dp.throttled(anti_flood)
async def arena_yes(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    address = call.data[6:]
    await nft_dao.edit_by_address(address=address, arena=True)
    db_session.commit()

    nft_data = await nft_dao.get_by_params(address=address)
    nft = nft_data[0]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_invite = InlineKeyboardButton(text="Пригласить на бой", switch_inline_query=f"{nft.name_nft}")
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_invite, kb_main_menu)
    await call.message.edit_text("Пригласите противника", reply_markup=keyboard)


async def search_game(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    nft_data = await nft_dao.get_by_params(user_id=call.from_user.id, arena=False)

    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(text=f"{nft.name_nft}", callback_data=f"nft_{nft.address}")
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    await call.message.edit_text("Выберите NFT для игры", reply_markup=keyboard)


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


@dp.throttled(anti_flood)
async def fight_yes(call: types.CallbackQuery):
    db_session = async_session()
    nft_dao = NftDAO(session=db_session)

    string = call.data
    split_result = string.split('_')
    opponent_id = split_result[1]  # ID link
    nft_address = split_result[2]  # NFT address

    nft_data = await nft_dao.get_by_params(user_id=opponent_id, arena=True)
    nft_opponent = nft_data[0]

    await nft_dao.edit_by_user_id(user_id=nft_link.user_id, arena=True)
    await nft_dao.edit_by_user_id(user_id=call.from_user.id, arena=True)
    await db_session.commit()
    # cursor.execute(f"UPDATE nfts SET arena=1 WHERE user={result[2]}")
    # cursor.execute(f"UPDATE nfts SET arena=1 WHERE user={call.from_user.id}")
    # conn.commit()

    # res = cursor.execute(
    #     f"SELECT address, rare, name_nft, user FROM nfts WHERE name_nft='{name_two}'").fetchone()  # TO LINK
    nft_data = await nft_dao.get_by_params(name_nft=name_two)
    nft_to_link: Nft = nft_link[0]

    chance = determine_winner(nft_link.rare * 10, nft_to_link.rare * 10, nft_link.user_id, nft_to_link.user_id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(main)
    client = TonApiClient("AFUY7GKTV35FWTQAAAADSRAF4LJ7EXUZZCTDJWBERXJIOBVQNDTO3W3S2UVN655L3JMTXWY")
    my_wallet_mnemonics = ['bleak', 'bag', 'clerk', 'artist', 'loop', 'tongue', 'middle', 'eternal', 'buzz', 'heavy',
                           'exile', 'such', 'fiber', 'frequent', 'flock', 'wrong', 'escape', 'stable', 'heart', 'burst',
                           'unfold', 'ticket', 'kangaroo', 'antenna']
    my_wallet = Wallet(provider=client, mnemonics=my_wallet_mnemonics, version='v4r2')

    vs = f"NFT:\n{nft_link.user_id} ⚔️ {nft_to_link.user_id}"
    if chance == 1:
        # print("Выиграл NFT №1")
        await bot.send_message(chat_id=result[2], text=f"Вы выиграли!\n\nСкоро NFT придёт на ваш адрес\n\n{vs}",
                               reply_markup=keyboard)
        await bot.send_message(chat_id=call.from_user.id, text=f"Вы проиграли!\n\n{vs}", reply_markup=keyboard)

        cursor.execute(f"UPDATE users SET win=win+1, bonus=bonus+1 WHERE user_id={result[2]}")
        cursor.execute(f"UPDATE users SET bonus=bonus-1 WHERE user_id={call.from_user.id}")
        conn.commit()

        # win = cursor.execute(f"SELECT address FROM users WHERE user_id={result[2]}").fetchone()
        user_data = await user_dao.get_by_params(user_id=nft_link.user_id)
        winner: User = user_data[0]
        # await transfer_nft(win[0], result[0])
        resp = await my_wallet.transfer_nft(destination_address=winner.address, nft_address=nft_to_link.address)
        # print(resp)  # 200
        await asyncio.sleep(25)
        resp = await my_wallet.transfer_nft(destination_address=winner.address, nft_address=nft_link.address)
    # print(resp)  # 200
    elif chance == 2:
        # print("Выиграл NFT №2")
        await bot.send_message(chat_id=nft_link.user_id, text=f"Вы проиграли!\n\n{vs}", reply_markup=keyboard)
        await bot.send_message(chat_id=call.from_user.id, text=f"Вы выиграли!\n\nСкоро NFT придёт на ваш адрес\n\n{vs}",
                               reply_markup=keyboard)

        cursor.execute(f"UPDATE users SET win=win+1, bonus=bonus+1 WHERE user_id={call.from_user.id}")
        cursor.execute(f"UPDATE users SET bonus=bonus-1 WHERE user_id={nft_link.user_id}")
        conn.commit()

        # win = cursor.execute(f"SELECT address FROM users WHERE user_id={call.from_user.id}").fetchone()
        user_data = await user_dao.get_by_params(user_id=call.from_user.id)
        winner: User = user_data[0]

        # await transfer_nft(win[0], res[0])
        resp = await my_wallet.transfer_nft(destination_address=winner.address, nft_address=nft_link.address)
        # print(resp)  # 200
        await asyncio.sleep(25)
        resp = await my_wallet.transfer_nft(destination_address=winner.address, nft_address=nft_to_link.address)
    # print(resp)  # 200
    else:
        await bot.send_message(chat_id=nft_link.user_id, text=f"Ничья!\n\n{vs}", reply_markup=keyboard)
        await bot.send_message(chat_id=call.from_user.id, text=f"Ничья!\n\n{vs}", reply_markup=keyboard)

        cursor.execute(f"UPDATE users SET bonus=bonus-1 WHERE user_id={nft_link.user_id}")
        cursor.execute(f"UPDATE users SET bonus=bonus-1 WHERE user_id={call.from_user.id}")
        conn.commit()

    # cursor.execute(f"DELETE FROM nfts WHERE address='{nft_link.address]}'")
    # cursor.execute(f"DELETE FROM nfts WHERE address='{address}'")
    # conn.commit()

    await nft_dao.delete_by_address(address=nft_link.address)
    await nft_dao.delete_by_address(address=address)
    await db_session.commit()


async def top_callback(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(main)

    cursor.execute(f"SELECT name, win FROM users ORDER BY win DESC LIMIT 10")
    result = cursor.fetchall()

    await call.message.edit_text(
        "Топ пользователь:{}".format("".join(["\n" + str(f"<b>%s</b> %s" % (row[0], row[1])) for row in result])),
        reply_markup=keyboard)


async def inline_handler(query: types.InlineQuery):
    text = query.query or "echo"
    result_id: str = hashlib.md5(text.encode()).hexdigest()

    id = query.from_user.id

    text = f"<a href='https://t.me/BATTLE_GAME_ANTIHERO_BOT'>TON ANTIHERO☢️</a>\nСразись с моим {text}\nНА АРЕНЕ."
    title = 'Пригласить на бой'
    description = "Пригласи друга в бой"

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    test = InlineKeyboardButton(text="Сразиться", url=f"http://t.me/Test_code_torkusz_bot?start={id}")
    keyboard.add(test)

    articles = [types.InlineQueryResultArticle(
        id=result_id,
        title=title,
        description=description,
        input_message_content=types.InputTextMessageContent(
            message_text=text),
        reply_markup=keyboard
    )]

    await query.answer(articles, cache_time=2, is_personal=True)


async def rel(message: types.Message):
    if message.from_user.id == 710140441:
        await message.reply(f"{message.chat.id}")


async def check(message: types.Message):
    if message.from_user.id == 710140441:
        await message.reply(f"{message}")
