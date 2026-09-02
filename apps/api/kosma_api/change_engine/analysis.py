"""The Change Engine's core logic: cohort match -> counterfactual replay ->
segmented metric comparison -> impact report with a SHIP/MODIFY/BLOCK
recommendation. This is the actual product (see PRODUCT-SPEC.md) - everything
else in the codebase is substrate feeding this."""

import math
import random
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from kosma_api.change_engine import llm_replay, mock_behavior
from kosma_api.change_engine.cohort import sample_cohort
from kosma_api.models.agent_config import AgentConfig
from kosma_api.models.change_proposal import ChangeProposal, ChangeProposalStatus
from kosma_api.models.impact_evidence import ImpactEvidence
from kosma_api.models.impact_report import MIN_SAMPLES_FOR_SIGNAL, ImpactReport, Recommendation
from kosma_api.models.project import Project
from kosma_api.models.trace import Trace, TraceSource, TraceStatus
from kosma_api.pricing import estimate_cost

# MIN_SAMPLES_FOR_SIGNAL (imported above) is a segment's minimum replayed
# sample count before its delta counts toward the recommendation - too few
# samples and a run of bad luck looks like a regression. This is a simple,
# stated threshold, not a real statistical test (see docs/architecture.md's
# "cohort statistics, not a trained model" decision and PRODUCT-SPEC.md's
# "never fabricate certainty" principle).
BLOCK_THRESHOLD = -0.15
MODIFY_THRESHOLD = -0.05


def _segment_metrics(baseline: list[Trace], replay_results: list[dict]) -> dict:
    n = len(baseline)
    baseline_success = sum(1 for t in baseline if t.success) / n
    replay_success = sum(1 for r in replay_results if r["success"]) / n
    baseline_tokens = sum(t.output_tokens for t in baseline) / n
    replay_tokens = sum(r["output_tokens"] for r in replay_results) / n
    return {
        "sample_size": n,
        "baseline_success_rate": round(baseline_success, 4),
        "candidate_success_rate": round(replay_success, 4),
        "success_delta": round(replay_success - baseline_success, 4),
        "baseline_avg_output_tokens": round(baseline_tokens, 1),
        "candidate_avg_output_tokens": round(replay_tokens, 1),
        "token_delta_pct": round((replay_tokens - baseline_tokens) / baseline_tokens, 4)
        if baseline_tokens
        else 0.0,
    }


def _recommendation(segment_metrics: list[dict]) -> tuple[Recommendation, float]:
    signals = [s for s in segment_metrics if s["sample_size"] >= MIN_SAMPLES_FOR_SIGNAL]

    # No segment cleared the sample-size bar: there's nothing to responsibly
    # base SHIP/MODIFY/BLOCK on. Saying SHIP here (the old behavior) would be
    # exactly the "fake intelligence when data is insufficient" this product
    # explicitly refuses to do - so say that plainly instead of guessing.
    if not signals:
        return Recommendation.INSUFFICIENT_EVIDENCE, 0.3

    worst_delta = min(s["success_delta"] for s in signals)
    total_samples = sum(s["sample_size"] for s in signals)

    if worst_delta <= BLOCK_THRESHOLD:
        recommendation = Recommendation.BLOCK
    elif worst_delta <= MODIFY_THRESHOLD:
        recommendation = Recommendation.MODIFY
    else:
        recommendation = Recommendation.SHIP

    # Confidence is a simple, stated function of total sample size - more
    # replayed executions, more confidence in the delta being real rather than
    # noise. Capped well short of 1.0: this is cohort statistics on mock data,
    # never asserted as certainty.
    confidence = round(min(0.92, 0.35 + 0.08 * math.sqrt(total_samples)), 2)
    return recommendation, confidence


def _real_replay_one(*, project: Project, candidate_config: AgentConfig, input_text: str) -> dict:
    """One real counterfactual execution: a real model call using the
    candidate's real prompt, then a real LLM-judge call scoring the result.
    Raises LLMReplayError on failure - callers must not fall back to a
    fabricated result when this was explicitly configured."""
    output_text, input_tokens, output_tokens = llm_replay.generate_candidate_output(
        provider=project.llm_provider,
        api_key=project.llm_api_key,
        model=candidate_config.model_name or "gpt-4o-mini",
        prompt_text=candidate_config.prompt_text or "",
        input_text=input_text,
    )
    success = llm_replay.judge_success(
        provider=project.llm_provider,
        api_key=project.llm_api_key,
        input_text=input_text,
        output_text=output_text,
    )
    return {
        "success": success,
        "output_tokens": output_tokens,
        "input_tokens": input_tokens,
        "output_text": output_text,
    }


def run_analysis(db: Session, change_proposal: ChangeProposal) -> ImpactReport:
    baseline_config = db.get(AgentConfig, change_proposal.baseline_config_id)
    candidate_config = db.get(AgentConfig, change_proposal.candidate_config_id)
    is_candidate = not candidate_config.is_baseline
    project = db.get(Project, change_proposal.project_id)

    use_real_replay = bool(
        project and project.llm_provider and project.llm_api_key and candidate_config.prompt_text
    )

    cohort = sample_cohort(
        db,
        agent_id=change_proposal.agent_id,
        baseline_config_id=baseline_config.id,
        seed=int(uuid.UUID(str(change_proposal.id))) % (2**32),
    )

    segment_metrics: list[dict] = []
    evidence_rows: list[ImpactEvidence] = []
    replay_traces: list[Trace] = []
    cohort_size = sum(len(v) for v in cohort.values())

    for segment, baseline_traces in cohort.items():
        if not baseline_traces:
            continue
        workflow, region = segment.split(":", 1)
        replay_results = []
        for i, baseline_trace in enumerate(baseline_traces):
            if use_real_replay:
                result = _real_replay_one(
                    project=project, candidate_config=candidate_config, input_text=baseline_trace.input_text
                )
                estimated_cost = estimate_cost(
                    db, project.llm_provider, candidate_config.model_name, result["input_tokens"], result["output_tokens"]
                )
            else:
                rng = random.Random(hash((str(change_proposal.id), baseline_trace.id, i)) % (2**32))
                result = mock_behavior.simulate(
                    workflow=workflow, region=region, is_candidate=is_candidate, rng=rng
                )
                estimated_cost = Decimal("0")
            replay_results.append(result)

            replay_trace = Trace(
                project_id=change_proposal.project_id,
                agent_id=change_proposal.agent_id,
                agent_config_id=candidate_config.id,
                trace_ref=f"replay-{change_proposal.id}-{baseline_trace.id}",
                workflow_tag=baseline_trace.workflow_tag,
                segment_tags=baseline_trace.segment_tags,
                input_text=baseline_trace.input_text,
                input_embedding=baseline_trace.input_embedding,
                status=TraceStatus.completed,
                success=result["success"],
                latency_ms=baseline_trace.latency_ms,
                input_tokens=baseline_trace.input_tokens,
                output_tokens=result["output_tokens"],
                total_tokens=baseline_trace.input_tokens + result["output_tokens"],
                estimated_cost=estimated_cost,
                model_provider=project.llm_provider if use_real_replay else baseline_trace.model_provider,
                model_name=candidate_config.model_name if use_real_replay else baseline_trace.model_name,
                source=TraceSource.replay,
            )
            db.add(replay_trace)
            db.flush()
            replay_traces.append(replay_trace)

            evidence_rows.append(
                ImpactEvidence(
                    segment=segment,
                    baseline_trace_id=baseline_trace.id,
                    replay_trace_id=replay_trace.id,
                    note=(
                        "regressed" if result["success"] is False and baseline_trace.success else None
                    ),
                )
            )

        metrics = _segment_metrics(baseline_traces, replay_results)
        metrics["segment"] = segment
        metrics["workflow"] = workflow
        metrics["region"] = region
        segment_metrics.append(metrics)

    overall = _segment_metrics(
        [t for group in cohort.values() for t in group],
        [
            {"success": rt.success, "output_tokens": rt.output_tokens}
            for rt in replay_traces
        ],
    )
    recommendation, confidence = _recommendation(segment_metrics)

    report = ImpactReport(
        change_proposal_id=change_proposal.id,
        cohort_size=cohort_size,
        sample_size=len(replay_traces),
        recommendation=recommendation,
        confidence=confidence,
        overall_metrics=overall,
        segment_metrics=segment_metrics,
        replay_method="real_llm" if use_real_replay else "mock",
    )
    db.add(report)
    db.flush()

    for evidence in evidence_rows:
        evidence.impact_report_id = report.id
        db.add(evidence)

    change_proposal.status = ChangeProposalStatus.analyzed
    db.commit()
    db.refresh(report)
    return report
