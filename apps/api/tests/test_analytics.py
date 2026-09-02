import uuid

from kosma_api.models.trace import Trace, TraceSource, TraceStatus


def _login(client):
    client.post("/v1/auth/login", json={"secret": "test-secret-123"})


def _seed_failed_trace(db_session, seeded_project, *, workflow, region):
    trace = Trace(
        project_id=seeded_project["project_id"],
        agent_id=seeded_project["agent_id"],
        agent_config_id=seeded_project["agent_config_id"],
        trace_ref=f"analytics-test-{uuid.uuid4().hex[:12]}",
        workflow_tag=workflow,
        segment_tags={"region": region},
        input_text="test",
        status=TraceStatus.completed,
        success=False,
        latency_ms=100,
        source=TraceSource.live,
    )
    db_session.add(trace)
    db_session.commit()


def test_failure_clusters_requires_auth(client):
    response = client.get("/v1/analytics/failure-clusters")
    assert response.status_code == 401


def test_failure_clusters_groups_by_workflow_and_region(client, seeded_project, db_session):
    for _ in range(3):
        _seed_failed_trace(db_session, seeded_project, workflow="refund", region="international")
    _seed_failed_trace(db_session, seeded_project, workflow="order_status", region="domestic")

    _login(client)
    response = client.get("/v1/analytics/failure-clusters")
    assert response.status_code == 200
    body = response.json()

    labels = {c["label"]: c for c in body["clusters"]}
    assert labels["refund:international"]["count"] >= 3
    assert labels["order_status:domestic"]["count"] >= 1
    # sorted worst-first
    counts = [c["count"] for c in body["clusters"]]
    assert counts == sorted(counts, reverse=True)
