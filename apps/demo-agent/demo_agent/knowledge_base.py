"""Fixed, small knowledge base for the demo customer-support agent. Not real
policy documents - deterministic demo content so retrieval spans have something
real to show in the trace explorer and cite in generated answers."""

DOCUMENTS = {
    "refund": [
        {
            "doc_id": "policy-refunds-v3",
            "title": "Refund Policy",
            "content": (
                "Orders may be refunded in full within 30 days of delivery. Domestic "
                "orders are refunded to the original payment method within 5 business "
                "days. International orders may incur customs/duties adjustments and "
                "require the customs declaration number before a refund is issued."
            ),
        },
        {
            "doc_id": "policy-shipping-v1",
            "title": "Shipping Policy",
            "content": (
                "Standard shipping takes 3-7 business days domestically and 10-21 "
                "business days internationally. Delays beyond these windows qualify "
                "for a refund or reshipment at the customer's choice."
            ),
        },
    ],
    "order_status": [
        {
            "doc_id": "policy-order-tracking-v2",
            "title": "Order Tracking",
            "content": (
                "Order status is available via the tracking tool and reflects the "
                "carrier's latest scan. Statuses are: processing, in_transit, "
                "delivered, delayed, or lost."
            ),
        },
    ],
    "account_change": [
        {
            "doc_id": "policy-account-changes-v1",
            "title": "Account Changes",
            "content": (
                "Customers may update shipping address, email, and payment method "
                "from account settings. Address changes only apply to orders that "
                "have not yet shipped."
            ),
        },
    ],
}


def retrieve(workflow: str) -> list[dict]:
    """Deterministic retrieval: returns this workflow's documents with plausible
    similarity/rerank scores. Retrieval quality itself isn't where the demo's
    injected regression lives (that's the generation step, see mock_provider.py) -
    this exists so the retrieval span and its evidence are real, inspectable data."""
    docs = DOCUMENTS[workflow]
    return [
        {
            "doc_id": d["doc_id"],
            "title": d["title"],
            "content": d["content"],
            "score": round(0.95 - 0.1 * i, 2),
            "rerank_score": round(0.93 - 0.08 * i, 2),
            "selected": i == 0,
        }
        for i, d in enumerate(docs)
    ]
