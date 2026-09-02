# kosma

Python SDK for sending AI agent execution traces to [Kosma](https://kosma-ai.vercel.app) -
lets Kosma's Blast Radius Diff, Failure Clusters, and Prediction Scorecard run on your
agent's real traffic instead of demo data.

## Install

```bash
pip install git+https://github.com/imraghavbansal/Kosma.git#subdirectory=packages/sdk
```

## Setup

Create a project from the Kosma dashboard (Projects &rarr; New project) to get an API
key, an `agent_id`, and an `agent_config_id`.

```bash
export KOSMA_API_KEY="kosma_live_..."
export KOSMA_API_URL="https://kosma-wb46.onrender.com"   # your deployment's API URL
```

## Quickstart

```python
from kosma import tracer

with tracer.start_trace(
    "customer-support-agent",
    agent_id="...",
    agent_config_id="...",
    workflow_tag="refund",
    segment_tags={"region": "international"},
    input_text="I'd like a refund for order #4471, it never arrived.",
) as t:
    t.set_model("openai", "gpt-4o-mini")

    with t.span("retrieval", span_type="retrieval") as retrieval:
        documents = [{"doc_id": "policy-refunds-v3", "score": 0.93, "selected": True}]
        retrieval.set_retrieval("refund policy", documents)

    with t.span("generate_response", span_type="llm") as generation:
        answer = "..."
        generation.set_output(answer=answer)

    t.set_usage(input_tokens=180, output_tokens=64)
    t.set_success(True)

print(t.trace_id)
```

Or wrap a whole function as one trace with the decorator form:

```python
from kosma import trace

@trace(name="research-agent", agent_id="...", agent_config_id="...")
def run_agent(query: str) -> str:
    ...
```

See [`examples/quickstart.py`](examples/quickstart.py) for a fuller example with nested
spans, a tool call, and a retrieval event.

## What each field means

- `agent_id` / `agent_config_id` - which agent and which version (prompt/model) produced
  this trace. Kosma compares traces across configs to measure a change's impact.
- `workflow_tag` / `segment_tags` - how Kosma buckets traces for the Blast Radius Diff
  (e.g. `workflow_tag="refund"`, `segment_tags={"region": "international"}`).
- `success` - did this execution do what it was supposed to. This is what "success rate"
  in the dashboard is computed from - set it deliberately, it's the signal the whole
  product runs on.

## Notes

- Retries on connection errors/timeouts with exponential backoff; a 4xx/5xx response is
  treated as a real rejection and raises `KosmaIngestError`, not retried.
- `trace_ref` (auto-generated as a UUID) is the ingestion idempotency key - retrying a
  `submit_trace` call with the same `trace_ref` after a timeout won't create a duplicate.
