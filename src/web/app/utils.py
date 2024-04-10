import hashlib
import hmac
from urllib import parse

from settings import settings


def validation(data_check_string: str, hash: str) -> bool:
    data_check_string = parse.unquote_plus(data_check_string)

    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=settings.TELEGRAM_API_KEY.get_secret_value().encode(),
        digestmod=hashlib.sha256,
    )

    hash_check = hmac.new(
        key=secret_key.digest(),
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    )

    if hash_check.hexdigest() != hash:
        return False
    return True
