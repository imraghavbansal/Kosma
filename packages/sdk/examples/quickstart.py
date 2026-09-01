"""Sends one real trace to a running Kosma API using the SDK's full surface:
the trace context manager, nested spans, a tool call, and a retrieval event.

Requires the API running locally (uvicorn kosma_api.main:app) and a project/agent/
config already created - see apps/api/scripts/create_dev_project.py.

Usage:
    KOSMA_API_KEY=... AGENT_ID=... AGENT_CONFIG_ID=... python examples/quickstart.py
"""

import os

from kosma import tracer

agent_id = os.environ["AGENT_ID"]
agent_config_id = os.environ["AGENT_CONFIG_ID"]

with tracer.start_trace(
    "customer-support-agent",
    agent_id=agent_id,
    agent_config_id=agent_config_id,
    workflow_tag="refund",
    segment_tags={"region": "international"},
    input_text="I'd like a refund for order #4471, it never arrived.",
) as t:
    t.set_model("mock", "mock-v1")

    with t.span("retrieval", span_type="retrieval") as retrieval:
        documents = [
            {"doc_id": "policy-refunds-v3", "title": "Refund Policy", "score": 0.93, "selected": True},
            {"doc_id": "policy-shipping-v1", "title": "Shipping Policy", "score": 0.41, "selected": False},
        ]
        retrieval.set_retrieval("refund policy for undelivered international order", documents)
        retrieval.set_output(selected_doc="policy-refunds-v3")

        with t.span("check_order_status", span_type="tool_call") as tool_span:
            order_status = {"status": "in_transit", "days_late": 6}
            tool_span.set_tool_call(
                "check_order_status", {"order_id": "4471"}, order_status, success=True
            )

    with t.span("generate_response", span_type="llm") as generation:
        answer = (
            "Your order is delayed in transit. Per our refund policy, since it's more "
            "than 5 days late, you're eligible for a full refund or reshipment."
        )
        generation.set_input(context_doc="policy-refunds-v3")
        generation.set_output(answer=answer)

    t.set_usage(input_tokens=180, output_tokens=64)

print(f"Trace submitted: trace_id={t.trace_id}")
