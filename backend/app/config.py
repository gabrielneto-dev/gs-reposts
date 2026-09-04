from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    softswitch_api_url: str
    softswitch_api_token: str
    softswitch_api_key: str

    database_url: str

    scheduler_enabled: bool = True
    scheduler_scan_limit: int = 10000
    scheduler_client_concurrency: int = 5
    scheduler_timezone: str = "America/Sao_Paulo"


settings = Settings()
