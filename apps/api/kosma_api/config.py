from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at the repo root (apps/api/kosma_api/config.py -> up 3 levels), not in
# apps/api/ - resolved absolutely so it's found regardless of the process's cwd
# (matters because uvicorn/pytest/alembic are documented to run from apps/api).
#
# In a container this path doesn't exist at all - the Docker build context is
# apps/api itself (see apps/api/Dockerfile), not the full repo, so there are
# only 1-2 parent directories, not 3, and no .env file is shipped in the image
# either (a host like Railway injects real environment variables directly, the
# correct production pattern - never bake secrets into an image). Guard with
# .exists() so pydantic-settings just reads from the process environment in
# that case instead of erroring on a path that doesn't resolve to anything.
_here = Path(__file__).resolve()
_REPO_ROOT_ENV_FILE = None
if len(_here.parents) > 3:
    _candidate_env_file = _here.parents[3] / ".env"
    if _candidate_env_file.exists():
        _REPO_ROOT_ENV_FILE = _candidate_env_file


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
    # Comma-separated. The browser only ever talks to the frontend's own origin
    # (see lib/api.ts's same-origin proxy) so this matters mainly for direct API
    # access (e.g. the /docs Swagger UI) from a deployed frontend origin.
    allowed_origins: str = Field(
        default="http://localhost:3000,https://kosma-ai.vercel.app",
        validation_alias="ALLOWED_ORIGINS",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    # GitHub OAuth: a second login method alongside the shared dashboard secret
    # (see kosma_api/routers/oauth.py's docstring for the scoping decision).
    github_client_id: str = Field(default="", validation_alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", validation_alias="GITHUB_CLIENT_SECRET")
    # Where GitHub redirects back to after authorizing - must exactly match the
    # OAuth App's registered callback URL.
    github_oauth_redirect_uri: str = Field(
        default="http://localhost:8000/v1/auth/github/callback",
        validation_alias="GITHUB_OAUTH_REDIRECT_URI",
    )
    # Where to send the browser after a successful login - the frontend's own
    # origin, not the API's.
    frontend_url: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")

    # GitHub App (separate from the OAuth App above): posts SHIP/MODIFY/BLOCK
    # verdicts as PR comments. Created in GitHub's UI, not by this app - see
    # routers/github_webhook.py's docstring for setup. Empty until configured;
    # the webhook endpoint returns 503 rather than silently no-op-ing.
    github_app_id: str = Field(default="", validation_alias="GITHUB_APP_ID")
    github_app_private_key: str = Field(default="", validation_alias="GITHUB_APP_PRIVATE_KEY")
    github_app_webhook_secret: str = Field(default="", validation_alias="GITHUB_APP_WEBHOOK_SECRET")


@lru_cache
def get_settings() -> Settings:
    return Settings()
