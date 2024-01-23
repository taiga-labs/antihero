from aiogram import Dispatcher
from aiogram.types import ContentType

from handler.handlers import start, select_nft, main, exit_game, add_nft, \
    wallet, get_nft_on_arena, remove_nft_from_arena, search, invite, search_game, nft_yes, callback_game_payment_prove, \
    arena_yes, fight_yes, inline_handler, top_callback, choose_wallet, connect_wallet
from utils.game import UserState


# bot handlers
def register_handlers_client(dp: Dispatcher) -> None:
    # Commands
    dp.register_message_handler(start, commands=["start"])
    # Listeners
    dp.register_inline_handler(inline_handler)
    # Callbacks
    dp.register_callback_query_handler(choose_wallet, text='choose_wallet')
    dp.register_callback_query_handler(connect_wallet, text_contains='connect:')



    dp.register_callback_query_handler(select_nft, state=UserState.nft)
    dp.register_callback_query_handler(callback_game_payment_prove, text_contains='game_')
    dp.register_callback_query_handler(main, text='main')
    dp.register_callback_query_handler(exit_game, text='exit')
    dp.register_callback_query_handler(add_nft, text='add_nft')
    dp.register_callback_query_handler(wallet, text='wallet')
    dp.register_callback_query_handler(get_nft_on_arena, text='nft_arena')
    dp.register_callback_query_handler(remove_nft_from_arena, text_contains='remove_')
    dp.register_callback_query_handler(search, text='Search')
    dp.register_callback_query_handler(invite, text='invite')
    dp.register_callback_query_handler(arena_yes, text_contains='arena_')
    dp.register_callback_query_handler(search_game, text='search_game')
    dp.register_callback_query_handler(nft_yes, text_contains='nft_')
    dp.register_callback_query_handler(fight_yes, text_contains='fight_')
    dp.register_callback_query_handler(top_callback, text='top')
