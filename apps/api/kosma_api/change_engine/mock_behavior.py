"""Deterministic behavior model used for counterfactual replay. Mirrors
apps/demo-agent/demo_agent/mock_provider.py's regression rule intentionally -
replay has to reflect the same "world" the historical corpus was generated
from, or a replayed comparison would be meaningless. Duplicated rather than
imported across the apps/demo-agent -> apps/api boundary so the API has no
runtime dependency on the demo app (see docs/architecture.md); the duplication
itself is a known, documented V1 simplification, not an oversight - see
docs/development-plan.md Phase 6 notes.

V1's Change Engine can only replay changes between agent_configs whose
behavior this module knows how to simulate - which for V1 means "baseline"
vs "the one candidate behavior profile" (see PRODUCT-SPEC.md's "Change types"
scope decision: prompt/model changes only, on the seeded demo agent). This is
honest about what it is: a demo of the mechanism, not a general-purpose
model-behavior simulator.
"""

import random

BASELINE_SUCCESS_RATE = 0.90
CANDIDATE_SUCCESS_RATE = 0.96
CANDIDATE_REGRESSION_SUCCESS_RATE = 0.40
REGRESSION_WORKFLOW = "refund"
REGRESSION_REGION = "international"


def simulate(*, workflow: str, region: str, is_candidate: bool, rng: random.Random) -> dict:
    """Returns {"success": bool, "output_tokens": int} for one counterfactual
    execution - same shape/logic as demo_agent.mock_provider.generate, minus the
    answer text (replay doesn't need to render a new answer, only the outcome)."""
    if is_candidate:
        if workflow == REGRESSION_WORKFLOW and region == REGRESSION_REGION:
            success_rate = CANDIDATE_REGRESSION_SUCCESS_RATE
        else:
            success_rate = CANDIDATE_SUCCESS_RATE
    else:
        success_rate = BASELINE_SUCCESS_RATE

    success = rng.random() < success_rate
    base_tokens = rng.randint(60, 110)
    output_tokens = int(base_tokens * 0.7) if is_candidate else base_tokens
    return {"success": success, "output_tokens": output_tokens}
