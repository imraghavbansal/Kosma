"""Direct unit tests for cohort selection: segment_key's pure key derivation,
and sample_cohort's grouping/stratified-sampling/source-filtering behavior,
called directly rather than through the HTTP layer (see test_change_engine.py
for the full HTTP flow that exercises this same code)."""

import uuid
from types import SimpleNamespace

from kosma_api.change_engine.cohort import MAX_PER_SEGMENT, sample_cohort, segment_key
from kosma_api.models.trace import Trace, TraceSource, TraceStatus


def test_segment_key_combines_workflow_and_region():
    trace = SimpleNamespace(workflow_tag="refund", segment_tags={"region": "international"})
    assert segment_key(trace) == "refund:international"


def test_segment_key_defaults_region_to_unknown_when_missing():
    trace = SimpleNamespace(workflow_tag="refund", segment_tags={})
    assert segment_key(trace) == "refund:unknown"


def _seed_trace(db_session, seeded_project, *, workflow, region, source=TraceSource.live):
    trace = Trace(
        project_id=seeded_project["project_id"],
        agent_id=seeded_project["agent_id"],
        agent_config_id=seeded_project["agent_config_id"],
        trace_ref=f"cohort-unit-{uuid.uuid4().hex[:12]}",
        workflow_tag=workflow,
        segment_tags={"region": region},
        input_text="test query",
        status=TraceStatus.completed,
        success=True,
        source=source,
    )
    db_session.add(trace)
    return trace


def test_sample_cohort_groups_by_segment(db_session, seeded_project):
    for _ in range(3):
        _seed_trace(db_session, seeded_project, workflow="refund", region="domestic")
    for _ in range(2):
        _seed_trace(db_session, seeded_project, workflow="order_status", region="international")
    db_session.commit()

    cohort = sample_cohort(
        db_session,
        agent_id=seeded_project["agent_id"],
        baseline_config_id=seeded_project["agent_config_id"],
        seed=1,
    )

    assert set(cohort.keys()) == {"refund:domestic", "order_status:international"}
    assert len(cohort["refund:domestic"]) == 3
    assert len(cohort["order_status:international"]) == 2


def test_sample_cohort_caps_each_segment_at_max_per_segment(db_session, seeded_project):
    for _ in range(MAX_PER_SEGMENT + 15):
        _seed_trace(db_session, seeded_project, workflow="refund", region="domestic")
    db_session.commit()

    cohort = sample_cohort(
        db_session,
        agent_id=seeded_project["agent_id"],
        baseline_config_id=seeded_project["agent_config_id"],
        seed=1,
    )

    assert len(cohort["refund:domestic"]) == MAX_PER_SEGMENT


def test_sample_cohort_excludes_non_live_traces(db_session, seeded_project):
    _seed_trace(db_session, seeded_project, workflow="refund", region="domestic", source=TraceSource.live)
    _seed_trace(db_session, seeded_project, workflow="refund", region="domestic", source=TraceSource.replay)
    db_session.commit()

    cohort = sample_cohort(
        db_session,
        agent_id=seeded_project["agent_id"],
        baseline_config_id=seeded_project["agent_config_id"],
        seed=1,
    )

    assert len(cohort["refund:domestic"]) == 1
