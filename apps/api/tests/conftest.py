import os

# DATABASE_URL intentionally not defaulted here - it comes from .env (Supabase
# connection string), same as the running app. Set it explicitly if running tests
# without a .env file present.
os.environ.setdefault("KOSMA_DASHBOARD_SECRET", "test-secret-123")
os.environ.setdefault("KOSMA_SESSION_SECRET_KEY", "test-session-signing-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from kosma_api.config import get_settings  # noqa: E402

get_settings.cache_clear()

from kosma_api.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def settings():
    return get_settings()
