from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings as _BaseSettings, SettingsConfigDict


class BaseSettings(_BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


class Config(_BaseSettings, extra="allow"):
    DEV: bool

    DATABASE_URL: PostgresDsn
    TONCONNECT_BROKER_URL: str
    GAME_BROKER_URL: str

    TELEGRAM_API_KEY: SecretStr

    WEBHOOK_HOST: str
    WEBHOOK_PATH: str
    WEBHOOK_PORT: int

    TELEGRAM_BOT_URL: str

    MINIAPP_HOST: str
    MINIAPP_PATH: str
    MINIAPP_PORT: int

    TON_API_KEY: SecretStr
    TONCENTER_API_KEY: SecretStr

    MANIFEST_URL: str
    MAIN_WALLET_MNEMONICS: SecretStr
    MAIN_WALLET_ADDRESS: str
    MAIN_COLLECTION_ADDRESS: str


settings = Config()
