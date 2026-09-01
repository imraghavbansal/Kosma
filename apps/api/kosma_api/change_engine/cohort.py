"""Cohort selection: given a baseline config, find the historical executions a
proposed change should be evaluated against. V1 matches on structured filters
(agent, config, workflow, region) rather than embedding similarity - the
seeded demo corpus's inputs are template-generated per workflow/region (see
apps/demo-agent/demo_agent/queries.py), so structured filters ARE the correct
match key here, not a simplification papering over missing embedding search.
input_embedding is still populated on ingestion (see kosma_api/embeddings.py)
and available for a real semantic-similarity cohort query once trace inputs
are genuinely free-text (V2, real LLM providers) rather than templated."""

import random
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.models.trace import Trace, TraceSource

MAX_PER_SEGMENT = 40


def segment_key(trace: Trace) -> str:
    region = trace.segment_tags.get("region", "unknown")
    return f"{trace.workflow_tag}:{region}"


def sample_cohort(db: Session, *, agent_id, baseline_config_id, seed: int) -> dict[str, list[Trace]]:
    """Returns {segment_key: [sampled traces]}, stratified so small segments
    (e.g. account_change+international) aren't crowded out by large ones
    (order_status+domestic) in a plain random sample - each segment present in
    the cohort gets its own bounded sample instead of one global draw."""
    traces = list(
        db.scalars(
            select(Trace).where(
                Trace.agent_id == agent_id,
                Trace.agent_config_id == baseline_config_id,
                Trace.source == TraceSource.live,
            )
        )
    )

    by_segment: dict[str, list[Trace]] = defaultdict(list)
    for trace in traces:
        by_segment[segment_key(trace)].append(trace)

    rng = random.Random(seed)
    sampled: dict[str, list[Trace]] = {}
    for key, group in by_segment.items():
        rng.shuffle(group)
        sampled[key] = group[:MAX_PER_SEGMENT]
    return sampled
