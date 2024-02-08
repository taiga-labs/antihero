import time
from base64 import urlsafe_b64encode

from aiogram import types
from aiogram.types import InlineKeyboardButton
from aioredis import Redis
from pytonconnect.exceptions import UserRejectsError
from sqlalchemy.ext.asyncio import AsyncSession
from tonsdk.boc import begin_cell
from tonsdk.utils import to_nano
from TonTools import *

from config.settings import settings
from create_bot import dp, bot, logger
from storage.dao.nfts_dao import NftDAO
from storage.dao.users_dao import UserDAO
from storage.schemas import NftModel
from utils.middleware import anti_flood
from utils.ton import get_nft_by_account, fetch_nft_by_address
from utils.wallet import get_connector


async def select_to_add_nft(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)

    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    user_nfts = await get_nft_by_account(user.address)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in user_nfts:
        name = nft.metadata.get('name')
        nft_address = nft.address.to_userfriendly()
        button = InlineKeyboardButton(text=f"{name}",
                                      callback_data=f"add_nft_{nft_address}")
        keyboard.add(button)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text("Выбери свою NFT, которую хочешь добавить", reply_markup=keyboard)


@dp.throttled(anti_flood, rate=10)
async def add_nft(call: types.CallbackQuery, db_session: AsyncSession, redis_session: Redis):
    user_dao = UserDAO(session=db_session)
    nft_dao = NftDAO(session=db_session)
    connector = await get_connector(chat_id=call.message.chat.id, broker=redis_session)
    await connector.restore_connection()
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]
    nft_address = call.data[8:]
    nft_name, nft_rare = await fetch_nft_by_address(nft_address=nft_address)
    body = bytes_to_b64str(NFTItem().create_transfer_body(new_owner_address=Address(settings.MAIN_WALLET_ADDRESS),
                                                          response_address=Address(
                                                              user.address)).to_boc())
    body = body.replace("+", '-').replace("/", '_')
    transaction = {
        'valid_until': int(time.time() + 300),
        'messages': [
            {
                'address': nft_address,
                'amount': to_nano(0.05, 'ton'),
                'payload': body
            }
        ]
    }
    await call.message.edit_text(text='Подтвердите перевод в приложении своего кошелька в течение 5 минут')
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    try:
        await asyncio.wait_for(connector.send_transaction(transaction=transaction), timeout=300)
    except asyncio.TimeoutError:
        await call.message.edit_text(text='Время подтверждения истекло',
                                     reply_markup=keyboard)
        connector.pause_connection()
        logger.info(f"add_nft | User {call.from_user.first_name}:{call.from_user.id} nft transfer timeout")
        return
    except UserRejectsError:
        await call.message.edit_text(text='Вы отменили перевод',
                                     reply_markup=keyboard)
        connector.pause_connection()
        logger.info(f"add_nft | User {call.from_user.first_name}:{call.from_user.id} nft transfer declined")
        return
    except Exception as e:
        await call.message.edit_text(text=f'Неизвестная ошибка! Обратитесь к администратору',
                                     reply_markup=keyboard)
        connector.pause_connection()
        logger.error(f"add_nft | User {call.from_user.first_name}:{call.from_user.id} error: {e}")
        return
    nft_model = NftModel(user_id=user.id,
                         address=nft_address,
                         name_nft=nft_name,
                         rare=nft_rare)
    await nft_dao.add(data=nft_model.model_dump())
    await db_session.commit()
    logger.info(f"add_nft | User {call.from_user.first_name}:{call.from_user.id} added nft {nft_name}:{nft_address}")

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_nft_prov = InlineKeyboardButton(text="Оплатить комиссию", callback_data=f"pay_fee_{nft_address}")
    keyboard.add(kb_nft_prov)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await bot.send_photo(chat_id=call.from_user.id,
                         photo=open(f'images/{nft_address}.png', 'rb'),
                         caption=f"Твоя NFT добавлена во внутренний кошелёк\n"
                                 f"Для активации NFT необходимо заплатить комиссию 0.1 TON",
                         reply_markup=keyboard)
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    connector.pause_connection()


async def select_to_activate_nft(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id, activated=False)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        kb_nft = InlineKeyboardButton(text=f"{nft.name_nft}",
                                      callback_data=f"show_nft_{nft.address}")
        keyboard.add(kb_nft)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text("Выбери NFT, которую хочешь активировать", reply_markup=keyboard)


async def show_nft(call: types.CallbackQuery):
    nft_address = call.data[9:]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_nft_prov = InlineKeyboardButton(text="Оплатить", callback_data=f"pay_fee_{nft_address}")
    keyboard.add(kb_nft_prov)
    kb_main_menu = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main_menu)
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)
    await bot.send_photo(chat_id=call.from_user.id,
                         photo=open(f'images/{nft_address}.png', 'rb'),
                         caption=f"Для активации NFT необходимо заплатить комиссию 0.1 TON",
                         reply_markup=keyboard)


@dp.throttled(anti_flood, rate=10)
async def pay_fee(call: types.CallbackQuery, db_session: AsyncSession, redis_session: Redis):
    nft_dao = NftDAO(session=db_session)

    connector = await get_connector(chat_id=call.message.chat.id, broker=redis_session)
    await connector.restore_connection()

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
    await call.message.edit_caption(
        caption='Подтвердите платёж в приложении своего кошелька в течение 5 минут')
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    try:
        await asyncio.wait_for(connector.send_transaction(transaction=transaction), timeout=300)
    except asyncio.TimeoutError:
        await call.message.edit_caption(
            caption='Время подтверждения истекло\n Повторно активировать NFT можно в разделе Кошелек',
            reply_markup=keyboard)
        connector.pause_connection()
        logger.info(f"pay_fee | User {call.from_user.first_name}:{call.from_user.id} nft {nft_address} activate timeout")
        return
    except UserRejectsError:
        await call.message.edit_caption(
            caption='Вы отменили перевод\n Повторно активировать NFT можно в разделе Кошелек',
            reply_markup=keyboard)
        connector.pause_connection()
        logger.info(f"pay_fee | User {call.from_user.first_name}:{call.from_user.id} nft {nft_address} activate declined")
        return
    except Exception as e:
        await call.message.edit_caption(
            caption=f'Неизвестная ошибка!\n Повторно активировать NFT можно в разделе Кошелек',
            reply_markup=keyboard)
        connector.pause_connection()
        logger.error(f"pay_fee | User {call.from_user.first_name}:{call.from_user.id} error: {e}")
        return

    await nft_dao.edit_by_address(address=nft_address, activated=True)
    await db_session.commit()

    await bot.send_message(chat_id=call.message.chat.id,
                           text=f"NFT активирована",
                           reply_markup=keyboard)
    await bot.delete_message(chat_id=call.message.chat.id,
                             message_id=call.message.message_id)

    connector.pause_connection()
    logger.info(f"pay_fee | User {call.from_user.first_name}:{call.from_user.id} has activated nft {nft_address}")


@dp.throttled(anti_flood)
async def get_nft_on_arena(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id, arena=True)

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
async def remove_nft_from_arena(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id, active=True)
    user = user_data[0]

    address = call.data[7:]
    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id, address=address)
    nft = nft_data[0]

    await nft_dao.edit_by_address(address=address, arena=False)
    await db_session.commit()

    logger.info(f"remove_nft_from_arena | User {call.from_user.first_name}:{call.from_user.id} remove nft {nft.name_nft}:{nft.address} from arena")

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_main = InlineKeyboardButton(text="Главное меню", callback_data="main")
    keyboard.add(kb_main)
    await call.message.edit_text(f"NFT {nft.name_nft} снята с арены", reply_markup=keyboard)
