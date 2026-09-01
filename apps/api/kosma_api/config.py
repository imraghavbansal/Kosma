from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at the repo root (apps/api/kosma_api/config.py -> up 3 levels), not in
# apps/api/ - resolved absolutely so it's found regardless of the process's cwd
# (matters because uvicorn/pytest/alembic are documented to run from apps/api).
_REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV_FILE, extra="ignore")

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
