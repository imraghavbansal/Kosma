"""Proves the seeded corpus's one deliberate regression is real and measurable,
not just a narrative claim in a docstring - see mock_provider.py."""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from demo_agent import mock_provider
from demo_agent.agent import REGIONS, WORKFLOWS
from demo_agent.mock_provider import REGION_WEIGHTS, WORKFLOW_WEIGHTS

TRIALS = 2000


def _success_rate(workflow: str, region: str, is_candidate: bool, seed: int) -> float:
    rng = random.Random(seed)
    successes = sum(
        1
        for _ in range(TRIALS)
        if mock_provider.generate(workflow=workflow, region=region, is_candidate=is_candidate, rng=rng)[
            "success"
        ]
    )
    return successes / TRIALS


def test_candidate_regresses_sharply_on_refund_international():
    baseline_rate = _success_rate("refund", "international", is_candidate=False, seed=1)
    candidate_rate = _success_rate("refund", "international", is_candidate=True, seed=1)

    assert baseline_rate > 0.85
    assert candidate_rate < 0.45
    assert baseline_rate - candidate_rate > 0.4


def test_candidate_does_not_regress_on_other_workflow_region_combinations():
    for workflow in WORKFLOWS:
        for region in REGIONS:
            if workflow == "refund" and region == "international":
                continue  # the one deliberate exception, covered above
            baseline_rate = _success_rate(workflow, region, is_candidate=False, seed=2)
            candidate_rate = _success_rate(workflow, region, is_candidate=True, seed=2)
            assert candidate_rate >= baseline_rate - 0.05, (
                f"unexpected regression on {workflow}/{region}: "
                f"baseline={baseline_rate:.2f} candidate={candidate_rate:.2f}"
            )


def test_candidate_overall_traffic_weighted_aggregate_looks_like_an_improvement():
    """This is the actual product thesis in one assertion: on the REAL traffic mix
    (see mock_provider.WORKFLOW_WEIGHTS / REGION_WEIGHTS - not an even split across
    combinations), aggregate success goes up under the candidate even though one
    segment collapses, which is exactly why a team might ship it without Kosma. An
    earlier version of this test used an even weight per combination and asserted
    the same claim - it failed, because a uniform average does not match the real
    traffic distribution the seeded corpus actually uses. Weighting matters."""
    combos = [(w, r) for w in WORKFLOWS for r in REGIONS]
    weights = {
        (w, r): WORKFLOW_WEIGHTS[w] * REGION_WEIGHTS[r] for w, r in combos
    }
    assert abs(sum(weights.values()) - 1.0) < 1e-9

    rng_baseline = random.Random(3)
    rng_candidate = random.Random(3)
    baseline_weighted = sum(
        weights[(w, r)] * _success_rate(w, r, is_candidate=False, seed=rng_baseline.randint(0, 1_000_000))
        for w, r in combos
    )
    candidate_weighted = sum(
        weights[(w, r)] * _success_rate(w, r, is_candidate=True, seed=rng_candidate.randint(0, 1_000_000))
        for w, r in combos
    )
    assert candidate_weighted > baseline_weighted


def test_candidate_uses_fewer_output_tokens_on_average():
    rng = random.Random(4)
    baseline_tokens = [
        mock_provider.generate(workflow="order_status", region="domestic", is_candidate=False, rng=rng)[
            "output_tokens"
        ]
        for _ in range(TRIALS)
    ]
    candidate_tokens = [
        mock_provider.generate(workflow="order_status", region="domestic", is_candidate=True, rng=rng)[
            "output_tokens"
        ]
        for _ in range(TRIALS)
    ]
    assert sum(candidate_tokens) / len(candidate_tokens) < sum(baseline_tokens) / len(baseline_tokens)
