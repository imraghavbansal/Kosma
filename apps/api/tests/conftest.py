import os

# DATABASE_URL intentionally not defaulted here - it comes from .env (Supabase
# connection string), same as the running app. Set it explicitly if running tests
# without a .env file present.
#
# TEST_DATABASE_URL, if set, overrides DATABASE_URL for this process only,
# before any app module reads settings - point it at a dedicated test Postgres
# project (see README's "Running the backend tests") so the suite's
# create-then-cascade-delete fixtures never touch real production data.
if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

os.environ.setdefault("KOSMA_DASHBOARD_SECRET", "test-secret-123")
os.environ.setdefault("KOSMA_SESSION_SECRET_KEY", "test-session-signing-key")

import secrets
import uuid

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from kosma_api.config import get_settings  # noqa: E402

get_settings.cache_clear()

from kosma_api.auth import hash_api_key  # noqa: E402
from kosma_api.db.session import SessionLocal  # noqa: E402
from kosma_api.main import app  # noqa: E402
from kosma_api.models.agent import Agent  # noqa: E402
from kosma_api.models.agent_config import AgentConfig, AgentConfigKind  # noqa: E402
from kosma_api.models.organization import Organization  # noqa: E402
from kosma_api.models.project import Project  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def settings():
    return get_settings()


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_project(db_session):
    """Creates a minimal org/project/agent/agent_config for a test to ingest traces
    against, and tears it down afterward (cascades to any traces/spans/etc. created
    during the test)."""
    raw_api_key = f"test-key-{secrets.token_hex(8)}"
    org = Organization(name=f"test-org-{uuid.uuid4().hex[:8]}")
    db_session.add(org)
    db_session.flush()

    project = Project(organization_id=org.id, name="test-project", api_key_hash=hash_api_key(raw_api_key))
    db_session.add(project)
    db_session.flush()

    agent = Agent(project_id=project.id, name="test-agent")
    db_session.add(agent)
    db_session.flush()

    config = AgentConfig(
        agent_id=agent.id,
        kind=AgentConfigKind.model,
        version_label="v1",
        model_provider="mock",
        model_name="mock-v1",
        is_baseline=True,
    )
    db_session.add(config)
    db_session.commit()

    yield {
        "org_id": org.id,
        "project_id": project.id,
        "agent_id": agent.id,
        "agent_config_id": config.id,
        "api_key": raw_api_key,
    }

    db_session.delete(org)  # cascades: project -> agents/traces/... , config
    db_session.commit()
