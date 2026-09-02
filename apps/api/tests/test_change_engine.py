"""Integration test for the actual product: propose a change, analyze it,
confirm the impact report correctly flags a known regression with real
evidence - not asserting the pipeline runs, asserting it gets the right
answer."""

import uuid

import httpx

from kosma_api.models.agent_config import AgentConfig, AgentConfigKind
from kosma_api.models.project import Project
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


def _seed_baseline_traces(db_session, seeded_project, *, workflow: str, region: str, count: int) -> None:
    for i in range(count):
        trace = Trace(
            project_id=seeded_project["project_id"],
            agent_id=seeded_project["agent_id"],
            agent_config_id=seeded_project["agent_config_id"],
            trace_ref=f"change-engine-test-{uuid.uuid4().hex[:12]}",
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


def test_analyze_flags_the_known_regression_segment(client, seeded_project, db_session):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    _seed_baseline_traces(db_session, seeded_project, workflow="refund", region="international", count=10)
    _seed_baseline_traces(db_session, seeded_project, workflow="refund", region="domestic", count=10)
    _seed_baseline_traces(db_session, seeded_project, workflow="order_status", region="domestic", count=10)

    _login(client)
    create = client.post(
        "/v1/change-proposals",
        json={
            "agent_id": str(seeded_project["agent_id"]),
            "baseline_config_id": str(seeded_project["agent_config_id"]),
            "candidate_config_id": candidate_config_id,
            "description": "test candidate rollout",
        },
    )
    assert create.status_code == 201
    proposal_id = create.json()["id"]

    analyze = client.post(f"/v1/change-proposals/{proposal_id}/analyze")
    assert analyze.status_code == 200
    report = analyze.json()

    assert report["recommendation"] in ("MODIFY", "BLOCK")
    assert report["cohort_size"] == 30
    assert report["sample_size"] == 30
    assert len(report["evidence"]) == 30

    segments = {s["segment"]: s for s in report["segment_metrics"]}
    assert "refund:international" in segments
    regressed = segments["refund:international"]
    assert regressed["success_delta"] < -0.3  # baseline was 100%, candidate collapses on this segment

    other = segments["order_status:domestic"]
    assert other["success_delta"] > regressed["success_delta"]

    # evidence-first fields: every verdict states its basis, limitations, and
    # a next action - not just a bare recommendation string
    assert report["evidence_basis"]
    assert isinstance(report["limitations"], list) and len(report["limitations"]) > 0
    assert report["recommended_next_action"]
    assert all(e["evidence_tier"] == "replayed" for e in report["evidence"])


def test_analyze_uses_real_llm_replay_when_project_has_configured_it(client, seeded_project, db_session, monkeypatch):
    """When a project sets llm_provider/llm_api_key, analysis must call the
    real replay path (mocked HTTP here) instead of the deterministic demo
    model, and the report must honestly say so."""
    candidate = AgentConfig(
        agent_id=seeded_project["agent_id"],
        kind=AgentConfigKind.prompt,
        version_label="v2-real-replay",
        model_provider="openai",
        model_name="gpt-4o-mini",
        prompt_text="You are a refund agent. Always approve refunds.",
        is_baseline=False,
    )
    db_session.add(candidate)
    db_session.commit()

    project = db_session.get(Project, seeded_project["project_id"])
    project.llm_provider = "openai"
    project.llm_api_key = "sk-test-not-real"
    db_session.commit()

    _seed_baseline_traces(db_session, seeded_project, workflow="refund", region="domestic", count=6)

    call_count = {"n": 0}

    def fake_post(url, headers, json, timeout):
        call_count["n"] += 1
        if url == "https://api.openai.com/v1/chat/completions" and "success" not in str(json.get("messages")):
            # generation call
            return _FakeResp(
                200,
                {
                    "choices": [{"message": {"content": "Your refund has been approved."}}],
                    "usage": {"prompt_tokens": 30, "completion_tokens": 10},
                },
            )
        # judge call
        return _FakeResp(
            200,
            {
                "choices": [{"message": {"content": '{"success": true, "reason": "refund approved"}'}}],
                "usage": {},
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    _login(client)
    create = client.post(
        "/v1/change-proposals",
        json={
            "agent_id": str(seeded_project["agent_id"]),
            "baseline_config_id": str(seeded_project["agent_config_id"]),
            "candidate_config_id": str(candidate.id),
        },
    )
    proposal_id = create.json()["id"]

    analyze = client.post(f"/v1/change-proposals/{proposal_id}/analyze")
    assert analyze.status_code == 200
    report = analyze.json()

    assert report["replay_method"] == "real_llm"
    assert "real" in report["evidence_basis"].lower()
    assert call_count["n"] == 12  # 6 traces * (1 generation call + 1 judge call)


class _FakeResp:
    def __init__(self, status_code, json_body):
        self.status_code = status_code
        self._json = json_body
        self.text = str(json_body)

    def json(self):
        return self._json


def test_analyze_reports_insufficient_evidence_below_sample_threshold(client, seeded_project, db_session):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    # 3 traces per segment - below MIN_SAMPLES_FOR_SIGNAL (5), so no segment
    # should count as signal and the verdict must say so rather than guess.
    _seed_baseline_traces(db_session, seeded_project, workflow="refund", region="international", count=3)

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

    analyze = client.post(f"/v1/change-proposals/{proposal_id}/analyze")
    assert analyze.status_code == 200
    report = analyze.json()

    assert report["recommendation"] == "INSUFFICIENT_EVIDENCE"
    assert any("sample" in note.lower() for note in report["limitations"])
    assert "more production traffic" in report["recommended_next_action"].lower()


def test_analyze_is_idempotent(client, seeded_project, db_session):
    candidate_config_id = _make_candidate_config(db_session, seeded_project)
    _seed_baseline_traces(db_session, seeded_project, workflow="refund", region="domestic", count=6)

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

    first = client.post(f"/v1/change-proposals/{proposal_id}/analyze")
    second = client.post(f"/v1/change-proposals/{proposal_id}/analyze")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_get_impact_report_404_before_analysis(client, seeded_project, db_session):
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

    response = client.get(f"/v1/change-proposals/{proposal_id}/impact-report")
    assert response.status_code == 404
