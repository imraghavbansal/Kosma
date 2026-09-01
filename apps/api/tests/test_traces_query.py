"""Covers GET /v1/traces list behavior specifically - filtering and pagination -
which test_ingestion.py's traces tests didn't exercise (those cover auth and the
detail endpoint's span tree)."""

import uuid


def _auth_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}


def _ingest(client, seeded_project, workflow_tag: str | None = None) -> None:
    payload = {
        "trace_ref": f"query-test-{uuid.uuid4().hex[:12]}",
        "agent_id": str(seeded_project["agent_id"]),
        "agent_config_id": str(seeded_project["agent_config_id"]),
        "workflow_tag": workflow_tag,
        "input_text": "test query",
        "latency_ms": 10,
        "spans": [],
    }
    response = client.post("/v1/traces", json=payload, headers=_auth_headers(seeded_project["api_key"]))
    assert response.status_code == 202


def test_list_traces_returns_total_and_items(client, seeded_project):
    for _ in range(3):
        _ingest(client, seeded_project, workflow_tag="refund")

    client.post("/v1/auth/login", json={"secret": "test-secret-123"})
    response = client.get("/v1/traces?limit=200")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    assert len(body["items"]) >= 3
    assert all("trace_ref" in item for item in body["items"])


def test_list_traces_filters_by_workflow_tag(client, seeded_project):
    _ingest(client, seeded_project, workflow_tag="refund")
    _ingest(client, seeded_project, workflow_tag="order_status")

    client.post("/v1/auth/login", json={"secret": "test-secret-123"})
    response = client.get("/v1/traces?workflow_tag=order_status&limit=200")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) >= 1
    assert all(item["workflow_tag"] == "order_status" for item in body["items"])


def test_list_traces_respects_limit_and_offset(client, seeded_project):
    for _ in range(5):
        _ingest(client, seeded_project, workflow_tag="refund")

    client.post("/v1/auth/login", json={"secret": "test-secret-123"})
    page1 = client.get("/v1/traces?workflow_tag=refund&limit=2&offset=0").json()
    page2 = client.get("/v1/traces?workflow_tag=refund&limit=2&offset=2").json()

    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    page1_ids = {item["id"] for item in page1["items"]}
    page2_ids = {item["id"] for item in page2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


def test_list_traces_orders_newest_first(client, seeded_project):
    _ingest(client, seeded_project, workflow_tag="account_change")
    _ingest(client, seeded_project, workflow_tag="account_change")

    client.post("/v1/auth/login", json={"secret": "test-secret-123"})
    body = client.get("/v1/traces?workflow_tag=account_change&limit=200").json()
    created_ats = [item["created_at"] for item in body["items"]]
    assert created_ats == sorted(created_ats, reverse=True)
