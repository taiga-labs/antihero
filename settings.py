from pydantic import PostgresDsn, SecretStr, RedisDsn, BaseModel
from pydantic_settings import BaseSettings as _BaseSettings, SettingsConfigDict


class BaseSettings(_BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )


class DatabaseSettings(BaseSettings):
    POSTGRES_DSN: PostgresDsn


class BrokerSettings(BaseSettings):
    TONCONNECT_REDIS_DSN: RedisDsn
    GAME_REDIS_DSN: RedisDsn
    GAME_CONNECTION_REDIS_DSN: RedisDsn


class TelegramBotSettings(BaseSettings):
    TELEGRAM_BOT_TOKEN: SecretStr

    USE_WEBHOOK: bool
    WEBHOOK_RESET: bool
    WEBHOOK_BASE_URL: str
    WEBHOOK_PATH: str
    WEBHOOK_PORT: str
    WEBHOOK_HOST: str
    DROP_PENDING_UPDATES: bool

    TELEGRAM_BOT_URL: str

    def build_webhook_url(self) -> str:
        return f"{self.WEBHOOK_BASE_URL}{self.WEBHOOK_PATH}"


class MiniAppSettings(BaseSettings):
    MINIAPP_HOST: str
    MINIAPP_PATH: str
    MINIAPP_PORT: int


class TonSettings(BaseSettings):
    TON_API_KEY: SecretStr
    TONCENTER_API_KEY: SecretStr

    MANIFEST_URL: str
    MAIN_WALLET_MNEMONICS: SecretStr
    MAIN_WALLET_ADDRESS: str
    MAIN_COLLECTION_ADDRESS: str


class AppConfig(BaseModel):
    database: DatabaseSettings
    broker: BrokerSettings
    telegram_bot: TelegramBotSettings
    miniapp: MiniAppSettings
    ton: TonSettings


config = AppConfig(
    database=DatabaseSettings(),
    broker=BrokerSettings(),
    telegram_bot=TelegramBotSettings(),
    miniapp=MiniAppSettings(),
    ton=TonSettings(),
)
