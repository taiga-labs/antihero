import hashlib
import hmac
from urllib import parse

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError

from settings import settings


def add_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Wrong data",
        )


def authentication(data_check_string: str, hash: str) -> bool:
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
