from pydantic import PostgresDsn, model_validator, SecretStr
from pydantic_settings import BaseSettings as _BaseSettings, SettingsConfigDict


class BaseSettings(_BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


class Config(_BaseSettings, extra="allow"):
    DEV: bool

    DATABASE_URL: PostgresDsn
    REDIS_URL: str

    TELEGRAM_API_KEY: SecretStr
    TELEGRAM_API_KEY_DEV: SecretStr

    WEBHOOK_HOST: str
    WEBHOOK_PATH: str
    WEBAPP_HOST: str
    WEBAPP_PORT: int

    TELEGRAM_BOT_URL: str
    TELEGRAM_BOT_URL_DEV: str

    MINIAPP_HOST: str
    MINIAPP_PORT: int
    CERT_FILE_PATH: str
    KEY_FILE_PATH: str

    TON_API_KEY: SecretStr
    TONCENTER_API_KEY: SecretStr

    MANIFEST_URL: str
    MAIN_WALLET_MNEMONICS: SecretStr
    MAIN_WALLET_ADDRESS: str
    MAIN_COLLECTION_ADDRESS: str

    @model_validator(mode='before')
    def validate_old_person(cls, values):
        if values['DEV'].lower() in ('true', '1', 't'):
            values['TELEGRAM_API_KEY'] = values['TELEGRAM_API_KEY_DEV']
            values['TELEGRAM_BOT_URL'] = values['TELEGRAM_BOT_URL_DEV']
        else:
            values['WEBHOOK_URL'] = f"{values['WEBHOOK_HOST']}{values['WEBHOOK_PATH']}"
        return values

    class Config:
        validate_assignment = True


settings = Config()
