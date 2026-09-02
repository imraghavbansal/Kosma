"""Command Center: the dashboard home's real question, "what needs attention" -
a triage view assembled from the same tables the rest of the product reads."""

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
            trace_ref=f"cc-test-{uuid.uuid4().hex[:12]}",
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


def test_command_center_requires_auth(client):
    response = client.get("/v1/command-center")
    assert response.status_code == 401


def test_command_center_lists_analyzed_proposal_as_waiting_for_review(client, settings, seeded_project, db_session):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    _seed_baseline_traces(db_session, seeded_project, workflow="refund", region="international", count=10)

    _login(client, settings)
    create = client.post(
        "/v1/change-proposals",
        json={
            "agent_id": str(seeded_project["agent_id"]),
            "baseline_config_id": str(seeded_project["agent_config_id"]),
            "candidate_config_id": candidate_config_id,
            "description": "command center test",
        },
    )
    proposal_id = create.json()["id"]
    client.post(f"/v1/change-proposals/{proposal_id}/analyze")

    response = client.get("/v1/command-center")
    assert response.status_code == 200
    body = response.json()

    waiting_ids = [p["id"] for p in body["waiting_for_review"]]
    assert proposal_id in waiting_ids

    matched = next(p for p in body["waiting_for_review"] if p["id"] == proposal_id)
    assert matched["recommendation"] in ("SHIP", "MODIFY", "BLOCK", "INSUFFICIENT_EVIDENCE")
    assert matched["agent_name"] == "test-agent"

    assert "prediction_accuracy" in body
    assert "calibration_rate" in body["prediction_accuracy"]


def test_scorecard_calibration_requires_auth(client):
    response = client.get("/v1/scorecard/calibration")
    assert response.status_code == 401


def test_scorecard_calibration_returns_shape(client, settings):
    _login(client, settings)
    response = client.get("/v1/scorecard/calibration")
    assert response.status_code == 200
    body = response.json()
    assert "total_predictions" in body
    assert "calibration_rate" in body
    assert "points" in body
