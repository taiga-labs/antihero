from aiogram import types
from aiogram.types import InlineKeyboardButton, ParseMode
from TonTools import *

from create_bot import dp
from handlers.handlers_menu import main_menu
from storage.dao.users_dao import UserDAO
from storage.driver import async_session, get_redis_async_client
from utils.middleware import anti_flood
from utils.wallet import get_connector


async def choose_wallet(call: types.CallbackQuery):
    redis = await get_redis_async_client()
    connector = await get_connector(chat_id=call.message.chat.id, broker=redis)
    wallets_list = connector.get_wallets()
    await redis.close()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for w in wallets_list:
        walet_button = InlineKeyboardButton(text=w['name'], callback_data=f'connect:{w["name"]}')
        keyboard.add(walet_button)
    await call.message.answer(text='Выбери кошелек для авторизации\n\n<i>Для отмены напиши</i>"<code>Отмена</code>"',
                              parse_mode=ParseMode.HTML,
                              reply_markup=keyboard)  # TODO fix отмена


@dp.throttled(anti_flood, rate=3)
async def connect_wallet(call: types.CallbackQuery):
    db_session = async_session()
    user_dao = UserDAO(session=db_session)

    redis = await get_redis_async_client()
    connector = await get_connector(chat_id=call.message.chat.id, broker=redis)
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
    await call.message.answer(text='У тебя есть 5 минут на подключение кошелька',
                              reply_markup=keyboard)

    for i in range(1, 300):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                wallet_address = connector.account.address
                wallet_address = Address(wallet_address).to_string(is_user_friendly=True, is_bounceable=False)
                await user_dao.edit_active_by_telegram_id(telegram_id=call.from_user.id, address=wallet_address)
                await db_session.commit()
                await call.message.answer(f'Успешная авторизация!\nАдрес кошелька:\n\n<code>{wallet_address}</code>',
                                          parse_mode=ParseMode.HTML)
                keyboard = await main_menu()
                await call.message.answer("Главное меню:", reply_markup=keyboard)

                # logger.info(f'Connected with address: {wallet_address}')  # TODO logger
            await redis.close()
            return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_retry = InlineKeyboardButton(text="Повторить", callback_data="choose_wallet")
    keyboard.add(kb_retry)
    await call.message.answer(f'Истекло время авторизации',
                              parse_mode=ParseMode.HTML,
                              reply_markup=keyboard)
    await redis.close()
