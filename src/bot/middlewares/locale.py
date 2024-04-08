from typing import Tuple, Any

from aiogram.contrib.middlewares.i18n import I18nMiddleware

from src.storage.dao.users_dao import UserDAO


class LocalizationMiddleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> str:
        *_, event, data = args
        language = "en"
        db_session = data["db_session"]
        user_dao = UserDAO(session=db_session)
        user_data = await user_dao.get_by_params(telegram_id=event.from_user.id)
        if user_data:
            user = user_data[0]
            language = user.language
        data["language"] = language
        return language
