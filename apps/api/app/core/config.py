from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Jamiu Legal Advisor"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] | str = "*"

    app_env: str = "development"

    # DATABASE
    database_url: str

    # AUTH / SECURITY
    secret_key: str
    access_token_expire_minutes: int = 60 * 24

    # OPENAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.2-mini"

    embedding_model: str = "text-embedding-3-small"
    rag_top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()