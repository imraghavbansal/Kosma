"""Integration tests for Phase 8 (regression suite generation) and Phase 9
(prediction scorecard) - the last two pieces of the core loop."""

import uuid

from kosma_api.models.agent_config import AgentConfig, AgentConfigKind
from kosma_api.models.trace import Trace, TraceSource, TraceStatus


def _login(client):
    client.post("/v1/auth/login", json={"secret": "test-secret-123"})


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


def _seed_traces(
    db_session, seeded_project, *, config_id, workflow, region, count, success, source=TraceSource.live
):
    for i in range(count):
        trace = Trace(
            project_id=seeded_project["project_id"],
            agent_id=seeded_project["agent_id"],
            agent_config_id=config_id,
            trace_ref=f"scorecard-test-{uuid.uuid4().hex[:12]}",
            workflow_tag=workflow,
            segment_tags={"region": region},
            input_text=f"test query {i}",
            status=TraceStatus.completed,
            success=success,
            latency_ms=100,
            input_tokens=80,
            output_tokens=60,
            total_tokens=140,
            source=source,
        )
        db_session.add(trace)
    db_session.commit()


def _propose_and_analyze(client, seeded_project, candidate_config_id):
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
    return proposal_id


def test_generate_regression_tests_from_worst_regression(client, seeded_project, db_session):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    # refund:international regresses under the candidate (mock_behavior's known rule)
    _seed_traces(
        db_session,
        seeded_project,
        config_id=seeded_project["agent_config_id"],
        workflow="refund",
        region="international",
        count=10,
        success=True,
    )

    _login(client)
    proposal_id = _propose_and_analyze(client, seeded_project, candidate_config_id)
    report = client.get(f"/v1/change-proposals/{proposal_id}/impact-report").json()

    gen = client.post(f"/v1/impact-reports/{report['id']}/regression-tests")
    assert gen.status_code == 201
    body = gen.json()
    assert body["total"] > 0
    for test in body["items"]:
        assert test["status"] == "pending"
        assert test["impact_report_id"] == report["id"]
        assert "refund" in test["expected_condition"]

    # idempotent - posting again doesn't duplicate
    gen2 = client.post(f"/v1/impact-reports/{report['id']}/regression-tests")
    assert gen2.json()["total"] == body["total"]

    listing = client.get("/v1/regression-tests").json()
    assert listing["total"] >= body["total"]


def test_ship_requires_analysis_first(client, seeded_project, db_session):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    _login(client)
    create = client.post(
        "/v1/change-proposals",
        json={
            "agent_id": str(seeded_project["agent_id"]),
            "baseline_config_id": str(seeded_project["agent_config_id"]),
            "candidate_config_id": candidate_config_id,
        },
    )
    proposal_id = create.json()["id"]

    ship = client.post(f"/v1/change-proposals/{proposal_id}/ship")
    assert ship.status_code == 422


def test_prediction_scorecard_reports_insufficient_data_without_live_candidate_traffic(
    client, seeded_project, db_session
):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    _seed_traces(
        db_session,
        seeded_project,
        config_id=seeded_project["agent_config_id"],
        workflow="order_status",
        region="domestic",
        count=6,
        success=True,
    )

    _login(client)
    proposal_id = _propose_and_analyze(client, seeded_project, candidate_config_id)
    client.post(f"/v1/change-proposals/{proposal_id}/ship")

    outcome = client.get(f"/v1/change-proposals/{proposal_id}/prediction-outcome")
    assert outcome.status_code == 200
    body = outcome.json()
    # no real live traffic under the candidate config exists yet - must say so,
    # not fabricate a comparison (see PRODUCT-SPEC.md "never fabricate certainty")
    for segment_result in body["actual_metrics"].values():
        assert segment_result["status"] == "insufficient_data"


def test_prediction_scorecard_compares_against_real_live_candidate_traffic(
    client, seeded_project, db_session
):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    _seed_traces(
        db_session,
        seeded_project,
        config_id=seeded_project["agent_config_id"],
        workflow="account_change",
        region="domestic",
        count=8,
        success=True,
    )
    # real post-ship-like live traffic under the candidate config
    _seed_traces(
        db_session,
        seeded_project,
        config_id=candidate_config_id,
        workflow="account_change",
        region="domestic",
        count=5,
        success=True,
        source=TraceSource.live,
    )

    _login(client)
    proposal_id = _propose_and_analyze(client, seeded_project, candidate_config_id)
    client.post(f"/v1/change-proposals/{proposal_id}/ship")

    outcome = client.get(f"/v1/change-proposals/{proposal_id}/prediction-outcome").json()
    segment_result = outcome["actual_metrics"]["account_change:domestic"]
    assert segment_result["sample_size"] == 5
    assert segment_result["actual_success_rate"] == 1.0
    assert "account_change:domestic" in outcome["prediction_error"]
