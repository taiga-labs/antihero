from io import BytesIO

import qrcode
from aiogram import types
from aiogram.types import InlineKeyboardButton, ParseMode
from TonTools import *
from aioredis import Redis
from pytonconnect import TonConnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.factories import dp, bot, logger
from src.bot.handlers.handlers_menu import main_menu
from src.storage.dao.users_dao import UserDAO
from src.utils.middleware import anti_flood
from src.utils.wallet import get_connector


async def choose_wallet(call: types.CallbackQuery):
    wallets_list = TonConnect.get_wallets()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for w in wallets_list:
        walet_button = InlineKeyboardButton(
            text=w["name"], callback_data=f'connect:{w["name"]}'
        )
        keyboard.add(walet_button)
    await call.message.answer(
        text="Выбери кошелек для авторизации", reply_markup=keyboard
    )


@dp.throttled(anti_flood, rate=3)
async def connect_wallet(
    call: types.CallbackQuery, db_session: AsyncSession, tonconnect_redis_session: Redis
):
    user_dao = UserDAO(session=db_session)

    connector = await get_connector(
        chat_id=call.message.chat.id, broker=tonconnect_redis_session
    )
    wallets_list = connector.get_wallets()
    wallet_name = call.data[8:]
    wlt = None

    for w in wallets_list:
        if w["name"] == wallet_name:
            wlt = w
            break
    if wlt is None:
        raise Exception(f"Unknown wallet: {wlt}")

    if wlt["name"] not in ["Tonkeeper"]:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        kb_retry = InlineKeyboardButton(text="Повторить", callback_data="choose_wallet")
        keyboard.add(kb_retry)
        await call.message.edit_text(
            f"На данный момент поддерживаюся только подключения через "
            f"<a href='https://tonkeeper.com/'>Tonkeeper</a>\n\n"
            f"Повторите попытку подключения",
            reply_markup=keyboard,
        )
        return

    generated_url = await connector.connect(wlt)

    img = qrcode.make(generated_url)
    stream = BytesIO()
    img.save(stream)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    url_button = InlineKeyboardButton(text="Подключить", url=generated_url)
    keyboard.add(url_button)
    await bot.delete_message(
        chat_id=call.from_user.id, message_id=call.message.message_id
    )
    wait_msg = await call.message.answer_photo(
        photo=stream.getvalue(),
        caption="Отсканируй QR код или нажми Подключить, чтобы начать авторизацию\n"
        "У тебя есть 5 минут на подключение кошелька",
        reply_markup=keyboard,
    )

    for i in range(1, 300):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                wallet_address = connector.account.address
                wallet_address = Address(wallet_address).to_string(
                    is_user_friendly=True, is_bounceable=False
                )
                wallet_address = wallet_address.replace("+", "-").replace("/", "_")
                await user_dao.edit_by_telegram_id(
                    telegram_id=call.from_user.id, address=wallet_address
                )
                await db_session.commit()
                keyboard = await main_menu()
                await bot.delete_message(
                    chat_id=wait_msg.chat.id, message_id=wait_msg.message_id
                )
                await call.message.answer(
                    text=f"Успешная авторизация!\nАдрес кошелька:\n\n<code>{wallet_address}</code>\n\nГлавное меню:",
                    reply_markup=keyboard,
                )
                logger.info(
                    f"connect_wallet | User {call.from_user.first_name}:{call.from_user.id} connected with address: {wallet_address}"
                )
            connector.pause_connection()
            return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_retry = InlineKeyboardButton(text="Повторить", callback_data="choose_wallet")
    keyboard.add(kb_retry)
    await bot.delete_message(chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
    await call.message.answer(
        f"Истекло время авторизации", parse_mode=ParseMode.HTML, reply_markup=keyboard
    )
    connector.pause_connection()
    logger.info(
        f"connect_wallet | User {call.from_user.first_name}:{call.from_user.id} connection timeout"
    )
