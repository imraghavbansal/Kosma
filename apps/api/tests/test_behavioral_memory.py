"""Behavioral Memory: searchable change -> outcome history. Real search over
real rows - no fabricated "similar historical change" narrative, just an
actual substring match against what's really in the database."""

import uuid

from kosma_api.models.agent_config import AgentConfig, AgentConfigKind
from kosma_api.models.trace import Trace, TraceSource, TraceStatus


def _login(client, settings):
    client.post("/v1/auth/login", json={"secret": settings.dashboard_secret})


def _make_candidate_config(db_session, seeded_project) -> str:
    candidate = AgentConfig(
        agent_id=seeded_project["agent_id"],
        kind=AgentConfigKind.prompt,
        version_label="v2-candidate",
        model_provider="mock",
        model_name="mock-v1",
        is_baseline=False,
    )
    db_session.add(candidate)
    db_session.commit()
    return str(candidate.id)


def _seed_baseline_traces(db_session, seeded_project, *, workflow: str, region: str, count: int) -> None:
    for i in range(count):
        trace = Trace(
            project_id=seeded_project["project_id"],
            agent_id=seeded_project["agent_id"],
            agent_config_id=seeded_project["agent_config_id"],
            trace_ref=f"bm-test-{uuid.uuid4().hex[:12]}",
            workflow_tag=workflow,
            segment_tags={"region": region},
            input_text=f"test query {i}",
            status=TraceStatus.completed,
            success=True,
            latency_ms=100,
            input_tokens=80,
            output_tokens=60,
            total_tokens=140,
            source=TraceSource.live,
        )
        db_session.add(trace)
    db_session.commit()


def test_behavioral_memory_requires_auth(client):
    response = client.get("/v1/behavioral-memory")
    assert response.status_code == 401


def test_search_finds_change_by_description_keyword(client, settings, seeded_project, db_session):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    _seed_baseline_traces(db_session, seeded_project, workflow="refund", region="international", count=10)

    _login(client, settings)
    create = client.post(
        "/v1/change-proposals",
        json={
            "agent_id": str(seeded_project["agent_id"]),
            "baseline_config_id": str(seeded_project["agent_config_id"]),
            "candidate_config_id": candidate_config_id,
            "description": "unique-marker-behavioral-memory-test",
        },
    )
    proposal_id = create.json()["id"]
    client.post(f"/v1/change-proposals/{proposal_id}/analyze")

    response = client.get("/v1/behavioral-memory", params={"q": "unique-marker-behavioral-memory-test"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == proposal_id
    assert body["items"][0]["worst_segment"] is not None


def test_search_finds_change_by_segment_keyword(client, settings, seeded_project, db_session):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    _seed_baseline_traces(db_session, seeded_project, workflow="account_change", region="domestic", count=10)

    _login(client, settings)
    create = client.post(
        "/v1/change-proposals",
        json={
            "agent_id": str(seeded_project["agent_id"]),
            "baseline_config_id": str(seeded_project["agent_config_id"]),
            "candidate_config_id": candidate_config_id,
        },
    )
    proposal_id = create.json()["id"]
    client.post(f"/v1/change-proposals/{proposal_id}/analyze")

    response = client.get("/v1/behavioral-memory", params={"q": "account_change"})
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert proposal_id in ids


def test_search_with_no_query_returns_everything(client, settings):
    _login(client, settings)
    response = client.get("/v1/behavioral-memory")
    assert response.status_code == 200
    body = response.json()
    assert body["query"] is None
    assert isinstance(body["items"], list)
