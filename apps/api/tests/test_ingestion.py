import uuid


def _auth_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}


def _unique_ref(label: str) -> str:
    # trace_ref is globally unique - random suffix avoids collisions across runs
    return f"{label}-{uuid.uuid4().hex[:12]}"


def test_ingest_rejects_missing_api_key(client):
    response = client.post("/v1/traces", json={})
    assert response.status_code == 401


def test_ingest_rejects_invalid_api_key(client):
    response = client.post("/v1/traces", json={}, headers=_auth_headers("not-a-real-key"))
    assert response.status_code == 401


def test_ingest_single_trace_no_spans(client, seeded_project):
    payload = {
        "trace_ref": _unique_ref("test-trace"),
        "agent_id": str(seeded_project["agent_id"]),
        "agent_config_id": str(seeded_project["agent_config_id"]),
        "input_text": "What is the refund policy?",
        "model_provider": "mock",
        "model_name": "mock-v1",
        "latency_ms": 120,
        "input_tokens": 50,
        "output_tokens": 30,
        "spans": [],
    }
    response = client.post("/v1/traces", json=payload, headers=_auth_headers(seeded_project["api_key"]))
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert "trace_id" in body


def test_ingest_trace_with_span_hierarchy_and_tool_call(client, seeded_project):
    payload = {
        "trace_ref": _unique_ref("test-trace"),
        "agent_id": str(seeded_project["agent_id"]),
        "agent_config_id": str(seeded_project["agent_config_id"]),
        "workflow_tag": "refund",
        "segment_tags": {"region": "international"},
        "input_text": "I want a refund for order 123",
        "model_provider": "mock",
        "model_name": "mock-v1",
        "status": "completed",
        "success": True,
        "latency_ms": 900,
        "input_tokens": 120,
        "output_tokens": 80,
        "spans": [
            {
                "ref": "retrieval",
                "span_type": "retrieval",
                "name": "retrieve_policy_docs",
                "latency_ms": 200,
                "retrieval_event": {
                    "query": "refund policy international",
                    "documents": [{"doc_id": "doc-1", "score": 0.91, "selected": True}],
                },
            },
            {
                "ref": "tool",
                "parent_ref": "retrieval",
                "span_type": "tool_call",
                "name": "check_order_status",
                "latency_ms": 150,
                "tool_call": {
                    "tool_name": "check_order_status",
                    "arguments": {"order_id": "123"},
                    "result": {"status": "delivered"},
                    "success": True,
                },
            },
            {
                "ref": "llm",
                "span_type": "llm",
                "name": "generate_response",
                "latency_ms": 550,
            },
        ],
    }
    response = client.post("/v1/traces", json=payload, headers=_auth_headers(seeded_project["api_key"]))
    assert response.status_code == 202
    trace_id = response.json()["trace_id"]

    get_response = client.post(
        "/v1/auth/login", json={"secret": "test-secret-123"}
    )
    assert get_response.status_code == 200

    detail = client.get(f"/v1/traces/{trace_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["workflow_tag"] == "refund"
    assert body["total_tokens"] == 200
    assert len(body["spans"]) == 3

    retrieval_span = next(s for s in body["spans"] if s["name"] == "retrieve_policy_docs")
    tool_span = next(s for s in body["spans"] if s["name"] == "check_order_status")
    assert tool_span["parent_span_id"] == retrieval_span["id"]
    assert len(retrieval_span["retrieval_events"]) == 1
    assert len(tool_span["tool_calls"]) == 1
    assert tool_span["tool_calls"][0]["tool_name"] == "check_order_status"


def test_ingest_rejects_unknown_parent_ref(client, seeded_project):
    payload = {
        "trace_ref": _unique_ref("test-trace"),
        "agent_id": str(seeded_project["agent_id"]),
        "agent_config_id": str(seeded_project["agent_config_id"]),
        "input_text": "test",
        "spans": [{"ref": "a", "parent_ref": "does-not-exist", "span_type": "llm", "name": "x"}],
    }
    response = client.post("/v1/traces", json=payload, headers=_auth_headers(seeded_project["api_key"]))
    assert response.status_code == 422


def test_list_traces_requires_dashboard_session(client):
    response = client.get("/v1/traces")
    assert response.status_code == 401


def test_get_trace_404_for_unknown_id(client):
    client.post("/v1/auth/login", json={"secret": "test-secret-123"})
    response = client.get("/v1/traces/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_ingest_is_idempotent_on_trace_ref(client, seeded_project):
    """A retried submission (same trace_ref, e.g. after a client-side timeout on a
    request that actually succeeded server-side) must not fail or create a second
    row - this is a real failure mode hit while seeding the demo corpus at volume,
    not a hypothetical."""
    payload = {
        "trace_ref": _unique_ref("idempotent"),
        "agent_id": str(seeded_project["agent_id"]),
        "agent_config_id": str(seeded_project["agent_config_id"]),
        "input_text": "retried submission",
        "spans": [],
    }
    first = client.post("/v1/traces", json=payload, headers=_auth_headers(seeded_project["api_key"]))
    second = client.post("/v1/traces", json=payload, headers=_auth_headers(seeded_project["api_key"]))

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["trace_id"] == second.json()["trace_id"]

    client.post("/v1/auth/login", json={"secret": "test-secret-123"})
    detail = client.get(f"/v1/traces/{first.json()['trace_id']}")
    assert detail.status_code == 200
    assert detail.json()["trace_ref"] == payload["trace_ref"]
