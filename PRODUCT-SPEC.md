# Kosma - Reconciled Master Specification (V1)

Status: approved scope, pre-implementation. Supersedes prior draft specs where they conflict.

## 1. Product identity

Kosma is an **AI Change Intelligence System**, not an observability, debugging, or RCA
platform. Those capabilities exist, but only as substrate feeding the actual product.

Tagline: **"Know what a change will break before you ship it."**

Core question the product answers:

> "Before I change my AI system, what behavior is this change likely to break?"

Core loop:

```
OBSERVE → LEARN → MODEL → PREDICT → SIMULATE → DECIDE → MEASURE → LEARN AGAIN
```

Flagship workflow:

```
ENGINEER PROPOSES CHANGE
  → Kosma finds comparable historical executions
  → runs counterfactual replay against a representative sample
  → produces an evidence-backed impact report, segmented by workflow
  → recommends SHIP / MODIFY / BLOCK with stated confidence
  → (once shipped) compares predicted vs actual outcome
```

## 2. What Kosma is explicitly NOT (V1)

- Not a Langfuse/LangSmith-style generic trace viewer as the primary surface.
- Not an OTLP-first observability backend (SDK-only ingestion for V1).
- Not a trained-ML forecasting product (V1 predictions are cohort statistics, not a
  model with real training signal - there is no training data on day one).
- Not multi-tenant SaaS with full org/user/RBAC (single-tenant, shared-secret auth).
- Not an autonomous-fix or auto-PR system (that's V3, explicitly deferred, and requires
  customer-controlled policy even then).

## 3. V1 scope decisions (approved)

| Decision | Chosen | Why |
|---|---|---|
| Change types | Prompt + model/config changes only | Cohort matching and replay are well-defined here. Retrieval/tool-schema changes need a much bigger feature space - V2. |
| Auth/tenancy | Single-tenant, shared-secret | Schema keeps `organization_id`/`project_id` so it isn't a rewrite later; no signup/login/RBAC UI to build now. |
| Ingestion | Kosma Python SDK only | Proves the core loop without building a spec-compliant OTLP collector. OTLP is V2, for interoperability. |
| Prediction method | Cohort statistics (match → replay → compare) | Fully honest with no training data; matches the "never fabricate certainty" principle. |
| AI calls | Mock provider only | Deterministic, zero-cost, clearly labeled DEMO DATA. Real provider abstraction exists in code but isn't exercised in V1. |
| Deployment | Local (docker compose) only | No hosting cost/infra for a portfolio-stage project. |

## 4. Entities cut or merged from the original specs, and why

| Original entity | Disposition |
|---|---|
| Users, RBAC, audit log | Cut - shared-secret auth covers V1's actual need |
| Deployment, AgentVersion | Merged into `agent_configs` (`kind` = prompt \| model, `version_label`) |
| Document (KB corpus w/ versioning) | Cut - retrieval events store documents inline as JSON; no KB versioning since retrieval changes are out of V1 scope |
| MemoryEvent | Cut - demo agent has no long-term memory system in V1 |
| Incident, Fix | Folded into `impact_reports` evidence + `regression_tests`; a dedicated incident workflow is V2 |
| Generic causal behavior graph | Cut - the one relationship V1 cares about (config → change proposal → impact report) is modeled directly via foreign keys, not a generic graph schema |
| RootCauseHypothesis / generic Evidence / Failure / NearMiss as five separate tables | Simplified into `evaluations`, `failure_clusters`, `failure_cluster_members` - enough to power evidence and "top failure patterns" without a full graph |

## 5. The three USPs V1 must prove

1. **Blast Radius Diff** - one visual per proposed change showing which workflows/segments
   gain vs lose, computed from real cohort replay.
2. **Prediction Scorecard** - every impact report is graded against actual post-ship
   outcome once available; Kosma's own forecasting accuracy becomes visible over time.
3. **Ship / Modify / Block gate** - the whole analysis collapses into one CI-check-shaped
   object (status + confidence + evidence), so Kosma reads like a gate a deploy process
   asks permission from, not a dashboard someone remembers to check.

## 6. Post-V1 direction (not built now)

- V1.5/V2: retrieval & tool-schema change types, OTLP ingestion, multi-user org/RBAC,
  automated regression execution against live deployments, GitHub/Slack/Jira integration,
  alerting, deployment-triggered baseline tracking.
- V3: "AI Reliability Engineer" - investigation → hypothesis → reproduction → proposed
  fix → regression tests → validation → PR, always human-approved, never autonomous.
- V4: Kosma as the general reliability control plane across agents, models, prompts,
  retrieval, memory, tools, deployments - continuously learning the customer's system.

See `docs/development-plan.md` for the phase-by-phase V1 build order and definition of done.
