"""The demo's mock LLM. Fully deterministic and rule-based - explicitly not a real
model, so demo metrics are never presented as real model behavior (see
PRODUCT-SPEC.md, "AI calls: Mock provider only").

This module is also where the seeded corpus's one deliberate regression lives, so
Phases 5-9 (cohort matching, counterfactual replay, the Blast Radius Diff) have a
real, measurable behavior difference to find - not a narrative claim. The rule is
written out explicitly below rather than hidden in a black box:

    baseline config:  ~90% success on every workflow/region combination.
    candidate config: ~96% success on every combination EXCEPT
                       (workflow="refund", region="international"), where it drops
                       to ~40%. With this segment's actual traffic share (see
                       seed.py's WORKFLOW_WEIGHTS/REGION_WEIGHTS - refund is 40% of
                       traffic, international is 20% of traffic, so this one
                       combination is ~8% of total volume), the TRAFFIC-WEIGHTED
                       aggregate success rate still comes out higher under the
                       candidate (~91.5%) than the baseline (90%) - verified in
                       tests/test_mock_provider.py, not just asserted here. The
                       regression only shows up once you segment by workflow and
                       region instead of looking at the one overall number. That
                       gap between the aggregate and the segmented reality is the
                       entire product thesis.

The story this maps to: the candidate prompt simplified refund-policy handling and
dropped the international customs/duties clause, so it now gives confidently wrong
answers to international refund requests while getting faster and cheaper (fewer
output tokens) everywhere else.
"""

import random

REGRESSION_WORKFLOW = "refund"
REGRESSION_REGION = "international"

BASELINE_SUCCESS_RATE = 0.90
CANDIDATE_SUCCESS_RATE = 0.96
CANDIDATE_REGRESSION_SUCCESS_RATE = 0.40

# Single source of truth for traffic distribution, imported by both seed.py (to
# actually generate the corpus) and tests/test_mock_provider.py (to verify the
# traffic-weighted aggregate claim above is real, not just asserted in a comment).
WORKFLOW_WEIGHTS = {"refund": 0.4, "order_status": 0.4, "account_change": 0.2}
REGION_WEIGHTS = {"domestic": 0.8, "international": 0.2}

GOOD_ANSWERS = {
    "refund": [
        "Based on our refund policy, you're eligible for a full refund. I've processed "
        "it to your original payment method; it should appear within 5 business days.",
        "You qualify for a refund under our 30-day policy. I've submitted the request "
        "and you'll see the credit shortly.",
    ],
    "order_status": [
        "Your order is currently in transit and on track for delivery within the "
        "standard shipping window.",
        "I checked the tracking - your order is being processed and will ship shortly.",
    ],
    "account_change": [
        "I've updated your account with the new information you provided.",
        "That change has been applied to your account successfully.",
    ],
}

BAD_ANSWERS = {
    # Deliberately wrong for the refund+international case: applies the domestic
    # refund timeline/process and never mentions customs, which is the actual
    # requirement per policy-refunds-v3 - a citation mismatch a human reviewer
    # would catch immediately, which is exactly the point.
    "refund": [
        "You're all set - I've refunded your order to your original payment method, "
        "it'll arrive in 5 business days.",
        "Refund approved. No further action needed on your end.",
    ],
    "order_status": [
        "I don't see any issues with your order.",
        "Your order should arrive soon.",
    ],
    "account_change": [
        "I've noted your request.",
        "That's been taken care of.",
    ],
}


def generate(
    *,
    workflow: str,
    region: str,
    is_candidate: bool,
    rng: random.Random,
) -> dict:
    """Returns {"answer", "success", "output_tokens"}."""
    if is_candidate:
        if workflow == REGRESSION_WORKFLOW and region == REGRESSION_REGION:
            success_rate = CANDIDATE_REGRESSION_SUCCESS_RATE
        else:
            success_rate = CANDIDATE_SUCCESS_RATE
    else:
        success_rate = BASELINE_SUCCESS_RATE

    success = rng.random() < success_rate
    pool = GOOD_ANSWERS[workflow] if success else BAD_ANSWERS[workflow]
    answer = rng.choice(pool)

    # Candidate config is modeled as cheaper/faster in general (fewer output
    # tokens) - part of why a team might ship it without checking segments first.
    base_tokens = rng.randint(60, 110)
    output_tokens = int(base_tokens * 0.7) if is_candidate else base_tokens

    return {"answer": answer, "success": success, "output_tokens": output_tokens}
