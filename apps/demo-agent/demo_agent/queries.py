"""Query templates the seed script samples from, per workflow and region, so the
generated corpus has realistic variety instead of one repeated string."""

import random

REFUND_DOMESTIC = [
    "I want a refund for order #{order_id}, it arrived damaged.",
    "Can I get my money back for order #{order_id}? It's not what I ordered.",
    "Requesting a refund on order #{order_id}, changed my mind.",
]

REFUND_INTERNATIONAL = [
    "I'd like a refund for order #{order_id}, it never arrived and I'm overseas.",
    "Order #{order_id} shipped internationally and is way overdue, refund please.",
    "Refund request for order #{order_id} - customs held it and I no longer want it.",
]

ORDER_STATUS_DOMESTIC = [
    "Where is my order #{order_id}?",
    "What's the status of order #{order_id}?",
    "Order #{order_id} tracking hasn't updated in days, what's going on?",
]

ORDER_STATUS_INTERNATIONAL = [
    "Where is my international order #{order_id}? It's been three weeks.",
    "Order #{order_id} shipped overseas, can you check the status?",
    "Tracking for order #{order_id} shows nothing since it left the country.",
]

ACCOUNT_CHANGE_DOMESTIC = [
    "I need to update my shipping address for order #{order_id}.",
    "Can you change the email on my account?",
    "I want to update my payment method before order #{order_id} ships.",
]

ACCOUNT_CHANGE_INTERNATIONAL = [
    "I need to update my customs declaration info for order #{order_id}.",
    "Can you change my shipping address, I'm relocating abroad?",
    "Update the payment method on file, my international card expired.",
]

_BY_WORKFLOW_REGION = {
    ("refund", "domestic"): REFUND_DOMESTIC,
    ("refund", "international"): REFUND_INTERNATIONAL,
    ("order_status", "domestic"): ORDER_STATUS_DOMESTIC,
    ("order_status", "international"): ORDER_STATUS_INTERNATIONAL,
    ("account_change", "domestic"): ACCOUNT_CHANGE_DOMESTIC,
    ("account_change", "international"): ACCOUNT_CHANGE_INTERNATIONAL,
}


def sample_query(workflow: str, region: str, rng: random.Random) -> tuple[str, str]:
    """Returns (input_text, order_id)."""
    order_id = str(rng.randint(10000, 99999))
    template = rng.choice(_BY_WORKFLOW_REGION[(workflow, region)])
    return template.format(order_id=order_id), order_id
