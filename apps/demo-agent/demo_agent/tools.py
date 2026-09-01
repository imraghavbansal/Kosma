"""Deterministic mock tools the agent calls mid-trace. Outputs are a function of
order_id + a seeded RNG, not real order data - this is DEMO DATA."""

import random

_STATUSES = ["processing", "in_transit", "delivered", "delayed"]


def check_order_status(order_id: str, region: str, rng: random.Random) -> dict:
    status = rng.choice(_STATUSES)
    days_in_transit = rng.randint(1, 25) if region == "international" else rng.randint(1, 10)
    return {"order_id": order_id, "status": status, "days_in_transit": days_in_transit}


def check_refund_eligibility(order_id: str, region: str, rng: random.Random) -> dict:
    eligible = rng.random() < 0.85
    reason = "within 30-day window" if eligible else "outside 30-day refund window"
    if region == "international" and eligible:
        reason += "; customs declaration on file"
    return {"order_id": order_id, "eligible": eligible, "reason": reason}
