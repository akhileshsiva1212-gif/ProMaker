from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = ""

    hindsight_base_url: str = ""
    hindsight_api_key: str = ""
    hindsight_bank_id: str = "promaker-product"

    app_env: str = "development"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    database_url: str = "sqlite+aiosqlite:///./data/promaker.db"

    @property
    def use_real_hindsight(self) -> bool:
        return bool(self.hindsight_base_url and self.hindsight_api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()