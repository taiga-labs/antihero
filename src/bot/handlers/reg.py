from aiogram import Dispatcher

from src.bot.handlers.handlers_wallet import choose_wallet, connect_wallet
from src.bot.handlers.handlers_game import (
    invite,
    arena_yes,
    search_game,
    duel_yes,
    fight_yes,
    exit_game,
)
from src.bot.handlers.handlers_menu import (
    start,
    inline_handler,
    wallet,
    search,
    top_callback,
    ping,
)
from src.bot.handlers.handlers_nft import (
    add_nft,
    select_to_add_nft,
    select_to_activate_nft,
    pay_fee,
    get_nft_on_arena,
    remove_nft_from_arena,
    show_nft,
    get_nft_withdrawable,
    withdraw_nft,
)
from src.storage.driver import async_session
from src.utils.middleware import (
    WalletNotConnectedMiddleware,
    DbSessionMiddleware,
    RedisSessionMiddleware,
)


# bot handlers
def register_handlers_client(dp: Dispatcher) -> None:
    # ping
    dp.register_message_handler(ping, commands=["ping"])

    # menu
    dp.register_message_handler(start, commands=["start"])
    # dp.register_callback_query_handler(main, text='main')  # registered by decorator
    dp.register_callback_query_handler(wallet, text="wallet")
    dp.register_callback_query_handler(search, text="Search")
    dp.register_callback_query_handler(top_callback, text="top")
    dp.register_inline_handler(inline_handler)

    # auth
    dp.register_callback_query_handler(choose_wallet, text="choose_wallet")
    dp.register_callback_query_handler(connect_wallet, text_contains="connect:")

    # nft
    dp.register_callback_query_handler(select_to_add_nft, text="select_nft")
    dp.register_callback_query_handler(add_nft, text_contains="add_nft_")
    dp.register_callback_query_handler(select_to_activate_nft, text="activate_nft")
    dp.register_callback_query_handler(show_nft, text_contains="show_nft_")
    dp.register_callback_query_handler(pay_fee, text_contains="pay_fee_")
    dp.register_callback_query_handler(get_nft_on_arena, text="nft_arena")
    dp.register_callback_query_handler(remove_nft_from_arena, text_contains="remove_")
    dp.register_callback_query_handler(get_nft_withdrawable, text="nft_withdrawable")
    dp.register_callback_query_handler(withdraw_nft, text_contains="withdraw_")

    # game
    dp.register_callback_query_handler(invite, text="invite")
    dp.register_callback_query_handler(arena_yes, text_contains="arena_")
    dp.register_callback_query_handler(search_game, text="search_game")
    dp.register_callback_query_handler(duel_yes, text_contains="nft_")
    dp.register_callback_query_handler(fight_yes, text_contains="fight_")
    dp.register_callback_query_handler(exit_game, text_contains="exit_")

    # mw
    dp.middleware.setup(WalletNotConnectedMiddleware())
    dp.middleware.setup(DbSessionMiddleware(session_pool=async_session))
    dp.middleware.setup(RedisSessionMiddleware())
