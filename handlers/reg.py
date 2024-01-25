from aiogram import Dispatcher

from handlers.handlers_auth import choose_wallet, connect_wallet
from handlers.handlers_game import invite, arena_yes, search_game, nft_yes, fight_yes, exit_game
from handlers.handlers_menu import start, inline_handler, wallet, search, top_callback, main, disconnect
from handlers.handlers_nft import add_nft, select_to_add_nft, select_to_activate_nft, pay_fee, get_nft_on_arena, \
    remove_nft_from_arena, show_nft
from utils.middleware import WalletConnectionMiddleware


# bot handlers
def register_handlers_client(dp: Dispatcher) -> None:
    # menu
    dp.register_message_handler(start, commands=["start"])
    dp.register_callback_query_handler(main, text='main')
    dp.register_callback_query_handler(wallet, text='wallet')
    dp.register_callback_query_handler(search, text='Search')
    dp.register_callback_query_handler(top_callback, text='top')
    dp.register_callback_query_handler(disconnect, text='disconnect')
    dp.register_inline_handler(inline_handler)

    # auth
    dp.register_callback_query_handler(choose_wallet, text='choose_wallet')
    dp.register_callback_query_handler(connect_wallet, text_contains='connect:')

    # nft
    dp.register_callback_query_handler(select_to_add_nft, text='select_nft')
    dp.register_callback_query_handler(add_nft, text_contains='add_nft_')
    dp.register_callback_query_handler(select_to_activate_nft, text='activate_nft')
    dp.register_callback_query_handler(show_nft, text_contains='show_nft_')
    dp.register_callback_query_handler(pay_fee, text_contains='pay_fee_')
    dp.register_callback_query_handler(get_nft_on_arena, text='nft_arena')
    dp.register_callback_query_handler(remove_nft_from_arena, text_contains='remove_')

    # game
    dp.register_callback_query_handler(invite, text='invite')
    dp.register_callback_query_handler(arena_yes, text_contains='arena_')
    dp.register_callback_query_handler(search_game, text='search_game')
    dp.register_callback_query_handler(nft_yes, text_contains='nft_')
    dp.register_callback_query_handler(fight_yes, text_contains='fight_')
    dp.register_callback_query_handler(exit_game, text='exit')

    # mw
    dp.middleware.setup(WalletConnectionMiddleware())
