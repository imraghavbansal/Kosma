import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://traceos:traceos@localhost:5434/traceos")
os.environ.setdefault("TRACEOS_DASHBOARD_SECRET", "test-secret-123")
os.environ.setdefault("TRACEOS_SESSION_SECRET_KEY", "test-session-signing-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from traceos_api.config import get_settings  # noqa: E402

get_settings.cache_clear()

from traceos_api.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def settings():
    return get_settings()
