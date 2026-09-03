"""Direct unit tests for the change engine's pure metric/recommendation logic -
no HTTP layer, no DB. See test_change_engine.py for the end-to-end integration
tests that exercise this same logic through the real API and a seeded cohort."""

from types import SimpleNamespace

from kosma_api.change_engine.analysis import _recommendation, _segment_metrics
from kosma_api.models.impact_report import MIN_SAMPLES_FOR_SIGNAL, Recommendation


def _trace(success: bool, output_tokens: int = 60):
    return SimpleNamespace(success=success, output_tokens=output_tokens)


def _replay(success: bool, output_tokens: int = 60):
    return {"success": success, "output_tokens": output_tokens}


def test_segment_metrics_computes_deltas():
    baseline = [_trace(True, 60), _trace(True, 60), _trace(False, 60), _trace(True, 60)]
    replay = [_replay(True, 90), _replay(True, 90), _replay(False, 90), _replay(False, 90)]

    metrics = _segment_metrics(baseline, replay)

    assert metrics["sample_size"] == 4
    assert metrics["baseline_success_rate"] == 0.75
    assert metrics["candidate_success_rate"] == 0.5
    assert metrics["success_delta"] == -0.25
    assert metrics["baseline_avg_output_tokens"] == 60.0
    assert metrics["candidate_avg_output_tokens"] == 90.0
    assert metrics["token_delta_pct"] == 0.5


def test_segment_metrics_guards_against_zero_baseline_tokens():
    baseline = [_trace(True, 0)]
    replay = [_replay(True, 10)]

    metrics = _segment_metrics(baseline, replay)

    assert metrics["token_delta_pct"] == 0.0


def test_recommendation_is_insufficient_evidence_below_sample_threshold():
    segment_metrics = [{"sample_size": MIN_SAMPLES_FOR_SIGNAL - 1, "success_delta": -0.9}]

    recommendation, confidence = _recommendation(segment_metrics)

    assert recommendation == Recommendation.INSUFFICIENT_EVIDENCE
    assert confidence == 0.3


def test_recommendation_blocks_on_large_regression():
    segment_metrics = [{"sample_size": MIN_SAMPLES_FOR_SIGNAL, "success_delta": -0.2}]

    recommendation, _ = _recommendation(segment_metrics)

    assert recommendation == Recommendation.BLOCK


def test_recommendation_modifies_on_moderate_regression():
    segment_metrics = [{"sample_size": MIN_SAMPLES_FOR_SIGNAL, "success_delta": -0.1}]

    recommendation, _ = _recommendation(segment_metrics)

    assert recommendation == Recommendation.MODIFY


def test_recommendation_ships_when_no_regression():
    segment_metrics = [{"sample_size": MIN_SAMPLES_FOR_SIGNAL, "success_delta": 0.0}]

    recommendation, _ = _recommendation(segment_metrics)

    assert recommendation == Recommendation.SHIP


def test_recommendation_uses_worst_segment_and_ignores_low_sample_segments():
    segment_metrics = [
        {"sample_size": MIN_SAMPLES_FOR_SIGNAL, "success_delta": 0.0},
        {"sample_size": MIN_SAMPLES_FOR_SIGNAL, "success_delta": -0.2},
        {"sample_size": MIN_SAMPLES_FOR_SIGNAL - 1, "success_delta": -0.9},  # excluded: too few samples
    ]

    recommendation, _ = _recommendation(segment_metrics)

    assert recommendation == Recommendation.BLOCK  # driven by -0.2, not the excluded -0.9


def test_recommendation_confidence_increases_with_sample_size_but_is_capped():
    small = _recommendation([{"sample_size": MIN_SAMPLES_FOR_SIGNAL, "success_delta": 0.0}])[1]
    large = _recommendation([{"sample_size": 500, "success_delta": 0.0}])[1]

    assert small < large <= 0.92
