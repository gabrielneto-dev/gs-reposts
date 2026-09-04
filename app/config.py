from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    softswitch_api_url: str
    softswitch_api_token: str
    softswitch_api_key: str


settings = Settings()
