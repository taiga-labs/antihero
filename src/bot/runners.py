from __future__ import annotations

from aiogram import Bot, Dispatcher, loggers

from settings import config
from src.bot.logger import logger


async def polling_startup(bots: list[Bot]) -> None:
    for bot in bots:
        await bot.delete_webhook(drop_pending_updates=config.telegram_bot.DROP_PENDING_UPDATES)
    if config.telegram_bot.DROP_PENDING_UPDATES:
        loggers.dispatcher.info("Updates skipped successfully")


async def webhook_startup(dispatcher: Dispatcher, bot: Bot) -> None:
    webhook_url: str = config.telegram_bot.build_webhook_url()
    if await bot.set_webhook(
        url=webhook_url,
        allowed_updates=dispatcher.resolve_used_update_types(),
        # secret_token=config.telegram_bot.WEBHOOK_SECRET_TOKEN,
        drop_pending_updates=config.common.DROP_PENDING_UPDATES,
    ):
        return loggers.webhook.info("Bot webhook successfully set on url '%s'", webhook_url)
    return loggers.webhook.error("Failed to set main bot webhook on url '%s'", webhook_url)


async def webhook_shutdown(bot: Bot) -> None:
    if not config.telegram_bot.WEBHOOK_RESET:
        return
    if await bot.delete_webhook():
        loggers.webhook.info("Dropped main bot webhook.")
    else:
        loggers.webhook.error("Failed to drop main bot webhook.")
    await bot.session.close()


def run_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    dispatcher.startup.register(polling_startup)
    logger.info(f"run_polling: start bot {bot.id}")
    return dispatcher.run_polling(bot)


def run_webhook(dispatcher: Dispatcher) -> None:
    dispatcher.startup.register(webhook_startup)
    dispatcher.shutdown.register(webhook_shutdown)
