from bot.runner import bot_start_polling, bot_start_webhook
from settings import settings

if settings.DEV:
    bot_start_polling()
else:
    bot_start_webhook()
