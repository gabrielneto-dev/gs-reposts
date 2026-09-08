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

    frontend_webhook_url: str | None = None
    frontend_alertas_webhook_url: str | None = None
    alerta_webhook_url: str | None = None


# Instância única — módulo reimportado do zero a cada restart do worker (`--reload` picks up
# .env changes indiretamente assim, já que ele mesmo só observa *.py).
settings = Settings()
