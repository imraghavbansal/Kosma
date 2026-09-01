from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    # Supabase Postgres connection string (Project Settings -> Database -> Connection
    # string, "Session pooler" or direct connection). No local Postgres/Docker for V1.
    database_url: str = "postgresql+psycopg://user:password@host:5432/postgres"
    dashboard_secret: str = Field(default="change-me", validation_alias="KOSMA_DASHBOARD_SECRET")
    session_cookie_name: str = "kosma_session"
    session_secret_key: str = Field(
        default="change-me-session-signing-key", validation_alias="KOSMA_SESSION_SECRET_KEY"
    )
    ai_provider: str = Field(default="mock", validation_alias="AI_PROVIDER")
    embedding_dim: int = 1536


@lru_cache
def get_settings() -> Settings:
    return Settings()
