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


DIRECTION_DEADBAND = 0.01  # deltas smaller than this count as "flat", not a direction


def _direction(delta: float) -> str:
    if delta < -DIRECTION_DEADBAND:
        return "regression"
    if delta > DIRECTION_DEADBAND:
        return "improvement"
    return "flat"


def compute_calibration_summary(db: Session) -> dict:
    """How much should you trust Kosma's predictions? Aggregates every
    prediction-outcome pair Kosma has ever produced (not just one change) into
    a real calibration number: for each segment where real live traffic
    existed to check against, did the predicted direction (regression /
    improvement / flat) match what actually happened. Segments with no live
    candidate traffic yet are excluded, not counted as correct or wrong -
    they're simply not evaluable."""
    outcomes = list(db.scalars(select(PredictionOutcome).where(PredictionOutcome.evaluated_at.is_not(None))))

    evaluated = 0
    correct = 0
    false_positives = 0  # predicted regression, actual was not
    false_negatives = 0  # predicted fine, actual regressed
    absolute_errors: list[float] = []
    points: list[dict] = []

    for outcome in outcomes:
        for segment, predicted in outcome.predicted_metrics.items():
            actual = outcome.actual_metrics.get(segment)
            if not actual or actual.get("status") == "insufficient_data":
                continue
            baseline_rate = predicted.get("baseline_success_rate", 0.0)
            actual_delta = actual["actual_success_rate"] - baseline_rate
            predicted_delta = predicted.get("success_delta", 0.0)

            predicted_dir = _direction(predicted_delta)
            actual_dir = _direction(actual_delta)
            is_correct = predicted_dir == actual_dir

            evaluated += 1
            if is_correct:
                correct += 1
            if predicted_dir == "regression" and actual_dir != "regression":
                false_positives += 1
            if predicted_dir != "regression" and actual_dir == "regression":
                false_negatives += 1
            absolute_errors.append(abs(outcome.prediction_error.get(segment, actual_delta - predicted_delta)))

            points.append(
                {
                    "change_proposal_id": str(outcome.change_proposal_id),
                    "segment": segment,
                    "predicted_direction": predicted_dir,
                    "actual_direction": actual_dir,
                    "correct": is_correct,
                    "predicted_delta": predicted_delta,
                    "actual_delta": round(actual_delta, 4),
                }
            )

    return {
        "total_predictions": len(outcomes),
        "segments_evaluated": evaluated,
        "segments_pending_live_data": sum(
            1
            for outcome in outcomes
            for a in outcome.actual_metrics.values()
            if a.get("status") == "insufficient_data"
        ),
        "correct_direction_count": correct,
        "calibration_rate": round(correct / evaluated, 4) if evaluated else None,
        "false_positive_count": false_positives,
        "false_negative_count": false_negatives,
        "mean_absolute_error": round(sum(absolute_errors) / len(absolute_errors), 4) if absolute_errors else None,
        "points": points,
    }
