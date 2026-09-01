# Kosma demo agent

A synthetic customer-support agent (refund, order status, account change) that
generates the historical trace corpus the rest of Kosma reasons about. Everything
it produces is DEMO DATA - clearly labeled as such throughout the product, never
presented as real production traffic or a real benchmark result.

## The scenario

Two agent configs exist:

- **`v1-baseline`** - the current production prompt. ~90% success across every
  workflow and region.
- **`v2-simplified-refund-policy`** - a candidate prompt that trimmed the
  refund-policy instructions to be faster/cheaper. It's ~94% successful
  overall, which reads as an improvement - except on refund requests from
  international customers, where it drops to ~20%, because it silently dropped
  the customs/duties handling the original prompt had. See
  `demo_agent/mock_provider.py` for the exact, deterministic rule this follows -
  it's written out in code, not hidden.

That gap between "looks better in aggregate" and "quietly broken for one
segment" is the whole reason Kosma exists. The seeded corpus exists so Phases
5-9 (cohort matching, counterfactual replay, the Blast Radius Diff, the
Ship/Modify/Block gate) have a real regression to find instead of a scripted
demo.

## Running it

Requires the API running locally and its virtualenv active (the seed script
imports `kosma_api` directly for DB access to backdate timestamps and for the
one-time project/agent/config setup):

```bash
cd apps/api
source .venv/bin/activate   # .venv/Scripts/activate on Windows
pip install -e ../../packages/sdk
uvicorn kosma_api.main:app &   # needs to be running for the SDK's HTTP calls

python ../demo-agent/demo_agent/seed.py
```

This creates one project/agent/two configs (credentials written to
`.demo_credentials.json`, gitignored) and ~1,700 traces: 1,400 under the
baseline config spread across the last 5-60 days, 300 under the candidate
config spread across the last 5 days (a "canary rollout"). It's deterministic -
rerunning with the same seed produces the same corpus - and prints a summary
table of success rate by config/workflow/region so the regression is visible
immediately, not just asserted.

## Tests

```bash
cd apps/demo-agent
python -m pytest tests/ -v
```

`tests/test_mock_provider.py` proves the regression is real: candidate success
rate on refund+international is measurably far below baseline, every other
workflow/region combination does not regress, and the overall aggregate success
rate still goes up under the candidate - which is exactly why segmenting by
workflow and region (not just looking at the aggregate) is the point.
