import asyncio
import json
import time
from base64 import urlsafe_b64encode

from aiogram import types
from aiogram.types import InlineKeyboardButton
from aioredis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from tonsdk.boc import begin_cell
from tonsdk.contract.token.nft import NFTItem
from tonsdk.utils import to_nano, Address, bytes_to_b64str
from TonTools.Contracts.Wallet import Wallet
from TonTools.Providers.TonCenterClient import TonCenterClient
from pytonconnect.exceptions import UserRejectsError

# from TonTools import *

from settings import settings
from src.bot.factories import dp, bot, logger, _
from src.storage.dao.nfts_dao import NftDAO
from src.storage.dao.users_dao import UserDAO
from src.storage.dao.withdrawals_dao import WithdrawalDAO
from src.storage.schemas import NftModel, WithdrawModel
from src.utils.exceptions import ProviderFailed
from src.utils.antiflood import anti_flood
from src.utils.ton import get_nft_by_account, fetch_nft_by_address
from src.utils.wallet import get_connector


async def select_to_add_nft(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)

    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    user_nfts = await get_nft_by_account(user.address)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in user_nfts:
        name = nft.metadata.get("name")
        nft_address = nft.address.to_userfriendly()
        button = InlineKeyboardButton(
            text=f"{name}", callback_data=f"add_nft_{nft_address}"
        )
        keyboard.add(button)
    kb_main_menu = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text(
        _("Выбери свою NFT, которую хочешь добавить"), reply_markup=keyboard
    )


@dp.throttled(anti_flood, rate=10)
async def add_nft(
    call: types.CallbackQuery, db_session: AsyncSession, tonconnect_redis_session: Redis
):
    user_dao = UserDAO(session=db_session)
    nft_dao = NftDAO(session=db_session)
    connector = await get_connector(
        chat_id=call.message.chat.id, broker=tonconnect_redis_session
    )
    await connector.restore_connection()
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]
    nft_address = call.data[8:]
    nft_name, nft_rare = await fetch_nft_by_address(nft_address=nft_address)
    body = bytes_to_b64str(
        NFTItem()
        .create_transfer_body(
            new_owner_address=Address(settings.MAIN_WALLET_ADDRESS),
            response_address=Address(user.address),
        )
        .to_boc()
    )
    body = body.replace("+", "-").replace("/", "_")
    transaction = {
        "valid_until": int(time.time() + 300),
        "messages": [
            {"address": nft_address, "amount": to_nano(0.05, "ton"), "payload": body}
        ],
    }
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main)

    await call.message.edit_text(
        text=_("Подтвердите перевод в приложении своего кошелька в течение 5 минут"),
        reply_markup=keyboard,
    )

    try:
        await asyncio.wait_for(
            connector.send_transaction(transaction=transaction), timeout=300
        )
    except asyncio.TimeoutError:
        await call.message.edit_text(
            text=_("Время подтверждения истекло"), reply_markup=keyboard
        )
        connector.pause_connection()
        logger.info(
            f"add_nft | User {call.from_user.first_name}:{call.from_user.id} nft transfer timeout"
        )
        return
    except UserRejectsError:
        await call.message.edit_text(
            text=_("Вы отменили перевод"), reply_markup=keyboard
        )
        connector.pause_connection()
        logger.info(
            f"add_nft | User {call.from_user.first_name}:{call.from_user.id} nft transfer declined"
        )
        return
    except Exception as e:
        await call.message.edit_text(
            text=_("Неизвестная ошибка! Обратитесь к администратору"),
            reply_markup=keyboard,
        )
        connector.pause_connection()
        logger.error(
            f"add_nft | User {call.from_user.first_name}:{call.from_user.id} error: {e}"
        )
        return

    if not await nft_dao.is_exists(address=nft_address):
        nft_model = NftModel(
            user_id=user.id, address=nft_address, name_nft=nft_name, rare=nft_rare
        )
        await nft_dao.add(data=nft_model.model_dump())
    else:
        await nft_dao.edit_by_address(address=nft_address, user_id=user.id)
    await db_session.commit()
    logger.info(
        f"add_nft | User {call.from_user.first_name}:{call.from_user.id} added nft {nft_name}:{nft_address}"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_nft_prov = InlineKeyboardButton(
        text=_("Оплатить комиссию"), callback_data=f"pay_fee_{nft_address}"
    )
    keyboard.add(kb_nft_prov)
    kb_main_menu = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main_menu)
    await bot.send_photo(
        chat_id=call.from_user.id,
        photo=open(f"images/{nft_address}.png", "rb"),
        caption=_(
            "Твоя NFT добавлена во внутренний кошелёк\n"
            "Для активации NFT необходимо заплатить комиссию 0.1 TON"
        ),
        reply_markup=keyboard,
    )
    await bot.delete_message(
        chat_id=call.from_user.id, message_id=call.message.message_id
    )
    connector.pause_connection()


async def select_to_activate_nft(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(
        user_id=user.id, withdraw=False, activated=False
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        kb_nft = InlineKeyboardButton(
            text=f"{nft.name_nft}", callback_data=f"show_nft_{nft.address}"
        )
        keyboard.add(kb_nft)
    kb_main_menu = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text(
        _("Выбери NFT, которую хочешь активировать"), reply_markup=keyboard
    )


async def show_nft(call: types.CallbackQuery):
    nft_address = call.data[9:]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_nft_prov = InlineKeyboardButton(
        text=_("Оплатить"), callback_data=f"pay_fee_{nft_address}"
    )
    keyboard.add(kb_nft_prov)
    kb_main_menu = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main_menu)
    await bot.delete_message(
        chat_id=call.from_user.id, message_id=call.message.message_id
    )
    await bot.send_photo(
        chat_id=call.from_user.id,
        photo=open(f"images/{nft_address}.png", "rb"),
        caption=_("Для активации NFT необходимо заплатить комиссию 0.1 TON"),
        reply_markup=keyboard,
    )


@dp.throttled(anti_flood, rate=10)
async def pay_fee(
    call: types.CallbackQuery, db_session: AsyncSession, tonconnect_redis_session: Redis
):
    nft_dao = NftDAO(session=db_session)

    connector = await get_connector(
        chat_id=call.message.chat.id, broker=tonconnect_redis_session
    )
    await connector.restore_connection()

    nft_address = call.data[8:]
    data = {
        "address": settings.MAIN_WALLET_ADDRESS,
        "amount": str(100000000),
        "payload": urlsafe_b64encode(
            begin_cell().store_uint(0, 32).store_string(nft_address).end_cell().to_boc()
        ).decode(),
    }
    transaction = {"valid_until": int(time.time() + 3600), "messages": [data]}

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    kb_main = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main)

    await call.message.edit_caption(
        caption=_("Подтвердите платёж в приложении своего кошелька в течение 5 минут"),
        reply_markup=keyboard,
    )

    try:
        await asyncio.wait_for(
            connector.send_transaction(transaction=transaction), timeout=300
        )
    except asyncio.TimeoutError:
        await call.message.edit_caption(
            caption=_("Время подтверждения истекло\n Повторно активировать NFT можно в разделе Кошелек"),
            reply_markup=keyboard,
        )
        connector.pause_connection()
        logger.info(
            f"pay_fee | User {call.from_user.first_name}:{call.from_user.id} nft {nft_address} activate timeout"
        )
        return
    except UserRejectsError:
        await call.message.edit_caption(
            caption=_("Вы отменили перевод\n Повторно активировать NFT можно в разделе Кошелек"),
            reply_markup=keyboard,
        )
        connector.pause_connection()
        logger.info(
            f"pay_fee | User {call.from_user.first_name}:{call.from_user.id} nft {nft_address} activate declined"
        )
        return
    except Exception as e:
        await call.message.edit_caption(
            caption=_("Неизвестная ошибка!\n Повторно активировать NFT можно в разделе Кошелек"),
            reply_markup=keyboard,
        )
        connector.pause_connection()
        logger.error(
            f"pay_fee | User {call.from_user.first_name}:{call.from_user.id} error: {e}"
        )
        return

    await nft_dao.edit_by_address(address=nft_address, activated=True)
    await db_session.commit()

    await bot.send_message(
        chat_id=call.message.chat.id,
        text=_("NFT <code>{nft_address}</code> активирована").format(nft_address=nft_address),
        reply_markup=keyboard,
    )
    await bot.delete_message(
        chat_id=call.from_user.id, message_id=call.message.message_id
    )

    connector.pause_connection()
    logger.info(
        f"pay_fee | User {call.from_user.first_name}:{call.from_user.id} has activated nft {nft_address}"
    )


@dp.throttled(anti_flood)
async def get_nft_on_arena(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(user_id=user.id, arena=True)

    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(
            text=f"{nft.name_nft}", callback_data=f"remove_{nft.address}"
        )
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text(
        _("Выберите NFT чтобы снять с арены"), reply_markup=keyboard
    )


@dp.throttled(anti_flood)
async def remove_nft_from_arena(call: types.CallbackQuery, db_session: AsyncSession):
    address = call.data[7:]
    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(address=address)
    nft = nft_data[0]

    await nft_dao.edit_by_address(address=nft.address, arena=False)
    await db_session.commit()

    logger.info(
        f"remove_nft_from_arena | User {nft.user.name}:{nft.user.telegram_id} remove nft {nft.name_nft}:{nft.address} from arena"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_main = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main)
    await call.message.edit_text(
        _("NFT {name_nft} снята с арены").format(name_nft=nft.name_nft), reply_markup=keyboard
    )


@dp.throttled(anti_flood)
async def get_nft_withdrawable(call: types.CallbackQuery, db_session: AsyncSession):
    user_dao = UserDAO(session=db_session)
    user_data = await user_dao.get_by_params(telegram_id=call.from_user.id)
    user = user_data[0]

    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(
        user_id=user.id, duel=False, arena=False, withdraw=False
    )

    buttons = []
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for nft in nft_data:
        button = InlineKeyboardButton(
            text=f"{nft.name_nft}", callback_data=f"withdraw_{nft.address}"
        )
        buttons.append(button)
    keyboard.add(*buttons)
    kb_main_menu = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main_menu)
    await call.message.edit_text(
        _("Выберите NFT чтобы вывести из игры\n\n"
          "NFT будет отправлена на адрес <code>{address}</code>").format(address=user.address),
        reply_markup=keyboard,
    )


@dp.throttled(anti_flood)
async def withdraw_nft(call: types.CallbackQuery, db_session: AsyncSession):
    withdrawal_dao = WithdrawalDAO(session=db_session)

    address = call.data[9:]
    nft_dao = NftDAO(session=db_session)
    nft_data = await nft_dao.get_by_params(address=address)
    nft = nft_data[0]

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    kb_main = InlineKeyboardButton(text=_("Главное меню"), callback_data="main")
    keyboard.add(kb_main)

    if nft.arena:
        return await call.message.edit_text(
            _("⛔ Вывод NFT {name_nft} отклонен\n"
              "Необходимо снять героя с арены").format(name_nft=nft.name_nft),
            reply_markup=keyboard,
        )
    if nft.duel:
        return await call.message.edit_text(
            _("⛔ Вывод NFT {name_nft} отклонен\n"
              "Герой сейчас в битве").format(name_nft=nft.name_nft),
            reply_markup=keyboard,
        )
    if nft.withdraw:
        return await call.message.edit_text(
            _("⛔ Вывод NFT {name_nft} отклонен\n"
              "NFT уже ожидает вывода из игры").format(name_nft=nft.name_nft),
            reply_markup=keyboard,
        )

    provider = TonCenterClient(key=settings.TONCENTER_API_KEY.get_secret_value())
    wallet_mnemonics = json.loads(settings.MAIN_WALLET_MNEMONICS.get_secret_value())
    wallet = Wallet(mnemonics=wallet_mnemonics, version="v4r2", provider=provider)

    try:
        withdraw_resp = await wallet.transfer_nft(
            destination_address=nft.user.address, nft_address=nft.address, fee=0.015
        )
        if withdraw_resp != 200:
            raise ProviderFailed(withdraw_resp)
    except (ProviderFailed, Exception) as ex:
        logger.error(
            f"withdraw_nft | transfer error | nft:{nft.address} -> user:{nft.user.address} | Error: {ex}"
        )
        return await call.message.edit_text(
            _("⚠ Упс...\n"
              "Ошибка при попытке перевода NFT {name_nft}\n\n"
              "Попробуйте позже")
            .format(name_nft=nft.name_nft),
            reply_markup=keyboard,
        )

    logger.info(
        f"withdraw_nft | provider bid accepted | nft:{nft.address} -> user:{nft.user.address}"
    )

    withdrawal_model = WithdrawModel(
        nft_address=nft.address, dst_address=nft.user.address
    )
    await withdrawal_dao.add(withdrawal_model.model_dump())
    await nft_dao.edit_by_address(
        address=nft.address, duel=False, arena=False, activated=False, withdraw=True
    )
    await db_session.commit()

    logger.info(
        f"withdraw_nft | User {nft.user.name} set withdraw pending nft:{nft.address} -> user:{nft.user.address}"
    )

    await call.message.edit_text(
        _("Перевод принят в обработку\n"
          "NFT {name_nft} скоро придет на ваш кошелек")
        .format(name_nft=nft.name_nft),
        reply_markup=keyboard,
    )
