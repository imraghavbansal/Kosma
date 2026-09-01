"""The demo customer-support agent itself: takes a query, retrieves policy docs,
calls a tool, generates an answer via the mock provider, all wrapped in a Kosma
trace with proper spans. This is what actually runs, per config, to produce the
seeded corpus - see seed.py."""

import random

from kosma import tracer
from kosma.client import KosmaClient

from demo_agent import knowledge_base, mock_provider, queries, tools

WORKFLOWS = ["refund", "order_status", "account_change"]
REGIONS = ["domestic", "international"]

_TOOL_BY_WORKFLOW = {
    "refund": "check_refund_eligibility",
    "order_status": "check_order_status",
    "account_change": "check_order_status",
}


def run_once(
    *,
    workflow: str,
    region: str,
    agent_id: str,
    agent_config_id: str,
    is_candidate: bool,
    client: KosmaClient,
    rng: random.Random,
) -> str:
    """Runs one synthetic customer-support interaction and submits it as a trace.
    Returns the trace_ref (used later to backdate created_at for realism, since
    the ingestion API intentionally doesn't accept a client-supplied timestamp -
    see seed.py)."""
    input_text, order_id = queries.sample_query(workflow, region, rng)

    with tracer.start_trace(
        "customer-support-agent",
        agent_id=agent_id,
        agent_config_id=agent_config_id,
        workflow_tag=workflow,
        segment_tags={"region": region},
        input_text=input_text,
        client=client,
    ) as t:
        t.set_model("mock", "mock-v1")

        with t.span("retrieval", span_type="retrieval") as retrieval:
            documents = knowledge_base.retrieve(workflow)
            retrieval.set_retrieval(input_text, documents)
            retrieval.set_output(selected_doc=documents[0]["doc_id"])

            tool_name = _TOOL_BY_WORKFLOW[workflow]
            with t.span(tool_name, span_type="tool_call") as tool_span:
                if tool_name == "check_refund_eligibility":
                    result = tools.check_refund_eligibility(order_id, region, rng)
                else:
                    result = tools.check_order_status(order_id, region, rng)
                tool_span.set_tool_call(tool_name, {"order_id": order_id}, result, success=True)

        with t.span("generate_response", span_type="llm") as generation:
            gen = mock_provider.generate(
                workflow=workflow, region=region, is_candidate=is_candidate, rng=rng
            )
            generation.set_input(context_doc=documents[0]["doc_id"])
            generation.set_output(answer=gen["answer"])

        t.set_usage(input_tokens=rng.randint(80, 160), output_tokens=gen["output_tokens"])
        t.set_success(gen["success"])

    return t.trace_ref
