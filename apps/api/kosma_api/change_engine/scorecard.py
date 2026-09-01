"""Closes the loop: once a change is shipped, compare the impact report's
predicted segment metrics against what real live traffic under the candidate
config actually did. This is the moat feature from PRODUCT-SPEC.md - Kosma
grading its own forecasting accuracy over time.

"Actual" here means genuinely different data than the prediction was built
from: the impact report replayed the candidate config against sampled
baseline-config traces (a controlled counterfactual), while this compares
against real traces that were actually submitted under the candidate config
through the normal ingestion path (source=live) - for the demo corpus, the
300-trace "canary" batch seeded alongside the baseline history. If a segment
has no live candidate traffic yet, it's reported as insufficient data rather
than fabricated - see PRODUCT-SPEC.md's "never fabricate certainty"."""

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.models.change_proposal import ChangeProposal
from kosma_api.models.impact_report import ImpactReport
from kosma_api.models.prediction_outcome import PredictionOutcome
from kosma_api.models.trace import Trace, TraceSource

MIN_ACTUAL_SAMPLES = 3


def compute_prediction_outcome(db: Session, change_proposal: ChangeProposal) -> PredictionOutcome | None:
    report = db.scalar(
        select(ImpactReport).where(ImpactReport.change_proposal_id == change_proposal.id)
    )
    if report is None:
        return None

    live_candidate_traces = list(
        db.scalars(
            select(Trace).where(
                Trace.agent_id == change_proposal.agent_id,
                Trace.agent_config_id == change_proposal.candidate_config_id,
                Trace.source == TraceSource.live,
            )
        )
    )
    by_segment: dict[str, list[Trace]] = defaultdict(list)
    for trace in live_candidate_traces:
        region = trace.segment_tags.get("region", "unknown")
        by_segment[f"{trace.workflow_tag}:{region}"].append(trace)

    predicted_by_segment = {s["segment"]: s for s in report.segment_metrics}

    actual_metrics: dict = {}
    prediction_error: dict = {}
    for segment, predicted in predicted_by_segment.items():
        actual_traces = by_segment.get(segment, [])
        if len(actual_traces) < MIN_ACTUAL_SAMPLES:
            actual_metrics[segment] = {"status": "insufficient_data", "sample_size": len(actual_traces)}
            continue

        actual_success_rate = sum(1 for t in actual_traces if t.success) / len(actual_traces)
        actual_metrics[segment] = {
            "sample_size": len(actual_traces),
            "actual_success_rate": round(actual_success_rate, 4),
        }
        prediction_error[segment] = round(
            actual_success_rate - predicted["candidate_success_rate"], 4
        )

    outcome = db.scalar(
        select(PredictionOutcome).where(PredictionOutcome.change_proposal_id == change_proposal.id)
    )
    if outcome is None:
        outcome = PredictionOutcome(change_proposal_id=change_proposal.id)
        db.add(outcome)

    outcome.predicted_metrics = predicted_by_segment
    outcome.actual_metrics = actual_metrics
    outcome.prediction_error = prediction_error
    outcome.evaluated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(outcome)
    return outcome
