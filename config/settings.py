from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DEV: bool

    DATABASE_URL: PostgresDsn

    TELEGRAM_API_KEY: str
    WEBHOOK_HOST: str
    WEBHOOK_PATH: str
    WEBHOOK_PORT: str
    PATH_CERT: str
    TELEGRAM_BOT_URL: str

    TON_API_KEY: str
    MAIN_WALLET_MNEMONICS: str
    MAIN_WALLET_ADDRESS: str
    MAIN_COLLECTION_ADDRESS: str


settings = Config()
