# Kosma Architecture (V1)

> **Revision (2026-08-26)**: local dev moved off Docker. Docker Desktop proved
> unreliable on the primary dev machine (`vpnkit-bridge handshake failed` - a known
> Docker Desktop/WSL2 networking fault, not something retrying fixes). Postgres+pgvector
> moved to Supabase (hosted; also sidesteps compiling pgvector from source for native
> Windows Postgres, which has no official prebuilt binary). Redis+Arq was dropped for V1
> in favor of in-process async background tasks - see the updated "Why background jobs"
> section below for the reasoning. `infra/docker-compose.yml` is kept as an optional
> containerized path, not the primary one; README's quick start is now Docker-free.

## 1. System diagram

```
┌────────────────────┐
│   DEMO AGENT        │  Python, uses Kosma SDK, deterministic mock model
│ (customer support)  │
└──────────┬──────────┘
           │ trace() / span()
           ▼
┌────────────────────┐
│   Kosma SDK        │  buffers a trace's spans/tool_calls/retrieval_events,
│ (packages/sdk)        │  submits as one payload on trace completion
└──────────┬──────────┘
           │ POST /v1/traces  (Bearer: project API key)
           ▼
┌────────────────────┐
│  Ingestion API        │  FastAPI - validate, hash-check key, write to Postgres,
│ (apps/api)             │  schedule an in-process background task
└──────────┬──────────┘
           │
           ▼
┌────────────────────┐
│ Supabase Postgres      │  hosted, pgvector pre-enabled
│ + pgvector              │
└──────────┬──────────┘
           ▲
           │ writes back
┌──────────┴──────────┐
│  Background task        │  asyncio.create_task, same process as the API - normalize →
│  (apps/api)               │  embed input (pgvector) → tag workflow/segment → lightweight
│                            │  failure/near-miss heuristics
└──────────┬──────────┘
           ▲
           │ cohort queries, change analysis
┌──────────┴──────────┐
│   Change Engine        │  cohort match → counterfactual replay (deterministic
│ (apps/api)               │  mock by default; a real OpenAI/Anthropic call per
│                           │  project that configures llm_provider+API key) →
│                           │  metric comparison, segmented → impact report
│                           │  (SHIP/MODIFY/BLOCK/INSUFFICIENT_EVIDENCE + confidence)
└──────────┬──────────┘
           │ REST (dashboard session cookie)
           ▼
┌────────────────────┐
│   Next.js Dashboard    │  Home = "Propose a Change" + Blast Radius Diff +
│ (apps/web)               │  Prediction Scorecard. Trace explorer/evidence = secondary nav.
└────────────────────┘
```

## 2. Why each major decision

Format: Problem → Options → Decision → Reason → Tradeoff.

### Why FastAPI (backend)

- **Problem**: need a typed, async-friendly API for ingestion + query + the change engine.
- **Options**: FastAPI, Flask, Django REST Framework.
- **Decision**: FastAPI.
- **Reason**: native async, Pydantic validation matches the trace/span payload shape well,
  automatic OpenAPI docs satisfy the API-contract requirement for free.
- **Tradeoff**: smaller ecosystem than Django for things Kosma doesn't need (admin UI,
  ORM batteries) - acceptable, SQLAlchemy fills the ORM gap.

### Why PostgreSQL + pgvector (no separate vector DB)

- **Problem**: need relational storage for traces/spans plus similarity search for cohort
  matching.
- **Options**: Postgres+pgvector, Postgres + separate vector DB (Pinecone/Weaviate/Qdrant).
- **Decision**: Postgres+pgvector, hosted on Supabase.
- **Reason**: V1's embedding volume (thousands of demo traces) doesn't need a dedicated
  vector engine; keeping cohort queries as normal SQL (`ORDER BY embedding <=> $1`) joined
  against structured filters (workflow, segment, config, time window) is simpler than
  federating two data stores for one query.
- **Tradeoff**: won't scale to tens of millions of vectors without work - acceptable, out
  of scope for a V1 proving one workflow.

### Why no dedicated graph database

- **Problem**: spec asked for relationships between prompts/models/tools/retrieval/outcomes.
- **Decision**: model the one relationship V1 actually needs (`agent_config` →
  `change_proposal` → `impact_report` → `impact_evidence` → `traces`) as plain foreign
  keys.
- **Reason**: V1's relationship graph is a shallow tree, not a general graph query problem.
  A graph DB would be solving a problem V1 doesn't have yet.
- **Tradeoff**: if V2 adds retrieval/tool/memory relationships, this may need revisiting -
  intentionally deferred, not designed around today.

### Why in-process background tasks, not Redis + Arq

- **Problem**: trace ingestion must stay fast; embedding, tagging, and change analysis
  are comparatively expensive and must not block the ingestion request.
- **Options**: Celery, RQ, Arq (all require a Redis broker), in-process asyncio
  background tasks (`asyncio.create_task`, no broker).
- **Decision**: in-process asyncio tasks. (Originally speced as Arq+Redis - revised
  2026-08-26 when Docker Desktop proved unreliable for local dev; see the note at the
  top of this document.)
- **Reason**: V1's actual job volume is a few thousand demo traces processed by one
  operator - durability across process restarts and horizontal worker scaling aren't
  real requirements at this scale. An extra broker (Redis, or a hosted stand-in like
  Upstash) buys nothing here that a plain background task doesn't already give: it
  frees the ingestion request immediately, and the work still finishes in the background.
- **Tradeoff**: a job in flight is lost if the API process restarts (no queue durability),
  and there's no multi-worker fan-out. Both are real limitations of an in-process
  approach - acceptable for V1's scale, and exactly the point at which Redis+Arq (or a
  hosted queue) would earn its keep in V2 if trace volume or reliability requirements
  grow past what one process can absorb.

### Why cohort statistics instead of a trained model

- **Problem**: "predict change impact" sounds like it wants an ML model.
- **Decision**: compute impact by matching a historical cohort and replaying the candidate
  config against a sample of it, then compare real before/after metrics.
- **Reason**: there is no training signal on day one for any customer (or the demo). A
  trained model here would either be fit to synthetic data (dishonest - it would just be
  memorizing the demo's seeded outcomes) or undertrained. Cohort comparison against real
  replayed executions is fully honest and matches the spec's explicit "never fabricate
  certainty" rule.
- **Tradeoff**: less "ML-flavored" for a portfolio; the counter is that the actual
  differentiator (cohort matching + counterfactual replay + segmented evidence) is
  the harder and more interesting systems problem, not the modeling problem.

### Why SDK-only ingestion (no OTLP in V1)

- **Problem**: spec wants OTLP as a first-class ingestion path for interoperability.
- **Decision**: build the Python SDK only for V1; OTLP is V2.
- **Reason**: an OTLP collector is meaningful, mostly orthogonal engineering effort that
  doesn't advance the actual differentiator (change impact analysis). The SDK is enough
  to populate a real, complete trace/span/tool/retrieval model.
- **Tradeoff**: can't ingest from an already-OTel-instrumented agent yet - acceptable,
  V2 item, and the internal trace model is designed so an OTLP adapter can map into it
  later without a schema change.

### Why single-tenant / shared-secret auth

- **Problem**: spec describes full multi-tenant org/user/RBAC/audit.
- **Decision**: keep `organizations` and `projects` tables (so the schema shape supports
  multi-tenancy later) but gate the dashboard with one shared secret
  (`KOSMA_DASHBOARD_SECRET`) and gate ingestion with a per-project hashed API key.
- **Reason**: this is a single-operator portfolio deployment; building real signup/login/
  RBAC is a lot of code that doesn't touch the product's actual thesis.
- **Tradeoff**: not production-multi-tenant - documented as a known V1 limitation.

### Why GitHub OAuth as a second login method, not per-user isolation

- **Problem**: a shared secret alone doesn't show "who's signed in," and a real login
  identity is a reasonable thing to want without committing to full multi-tenancy.
- **Decision**: added GitHub OAuth (`routers/oauth.py`) as a second, equally privileged
  login method. Signing in creates a real `users` row and a real session, but that
  session still explores the same shared seeded demo data every session does.
- **Reason**: building real per-user data isolation means re-scoping every existing
  endpoint (traces, agents, change proposals, ...) by tenant - genuine V2-scale work,
  not something to half-do. What's real here is the OAuth handshake, the user record,
  and the session; what's intentionally narrow is what that session unlocks.
- **Tradeoff**: two users signed in via GitHub see the same data, not their own -
  documented, not hidden. Once signed in, a GitHub-authenticated user can also link a
  project to their real GitHub repo and see its live commits/PRs (`routers/github.py`).

### Why the GitHub App PR bot surfaces the latest verdict instead of analyzing the diff

- **Problem**: the obvious next step for a PR bot is "read the diff, decide if it's an
  AI change, analyze it." Deciding what counts as a prompt/config change from a raw
  diff is repo-specific and genuinely unsolved in general.
- **Decision**: on a `pull_request` webhook event for a repo linked to a Kosma project,
  `routers/github_webhook.py` posts that project's most recently analyzed change
  proposal's verdict as a PR comment, rather than running a fresh analysis from the
  diff.
- **Reason**: surfacing real, already-computed evidence is honest; guessing at diff
  classification to trigger a new analysis would not be.
- **Tradeoff**: the PR comment isn't necessarily about the code in that specific PR -
  it's the latest verdict for the project. Acceptable for V1; diff-aware triggering is
  a real V2 problem, not faked here.

### Why a modular monolith, not microservices

- Same reasoning as the original spec: one FastAPI app (`apps/api`) with clearly
  separated modules (`ingestion/`, `change_engine/`, `analytics/`, `background/`) rather
  than separate deployable services. Splitting services adds operational overhead with
  no benefit at this scale.

## 3. Repository structure

```
kosma/
  apps/
    web/                    # Next.js dashboard (TypeScript, Tailwind, shadcn/ui)
    api/                    # FastAPI backend
      kosma_api/
        ingestion/           # POST /v1/traces, auth, payload validation
        change_engine/       # cohort matching, mock + real LLM replay, impact report, ship/measure
        analytics/           # failure clusters
        routers/              # all API endpoints (projects, agents, traces, change engine,
                               #   behavioral memory, command center, scorecard, GitHub OAuth
                               #   + activity, GitHub App webhook, public stats, auth)
        models/               # SQLAlchemy models
        schemas/              # Pydantic schemas
        background/             # in-process background tasks (embed, tag, analyze)
        db/                    # session, migrations entrypoint
      alembic/
      tests/
    demo-agent/              # seeded customer-support agent + seed script
  packages/
    sdk/                     # kosma Python SDK (pip-installable)
      kosma/
        trace.py
        span.py
        client.py
      tests/
  infra/
    docker-compose.yml        # optional containerized path, not the primary local flow
  docs/
    architecture.md
    database-schema.md
    api-design.md
    development-plan.md
    design-decisions/
  PRODUCT-SPEC.md
  README.md
  .env.example
```

## 4. Data flow (end to end)

```
1. demo-agent handles a synthetic customer request
2. SDK's trace() context manager records spans (query processing, retrieval,
   tool calls, LLM generation) with timestamps, tokens, model, workflow tag
3. On trace completion, SDK POSTs the full trace payload to the Ingestion API
4. Ingestion API validates the project API key, writes trace+spans+tool_calls+
   retrieval_events rows, schedules an in-process background task, returns 202
   immediately
5. Background task: embeds the trace's input text (pgvector), assigns workflow/segment
   tags if not already explicit, runs deterministic failure/near-miss checks,
   updates the trace row
6. Developer opens the dashboard, registers a candidate agent_config (new
   prompt or model version), creates a change_proposal referencing baseline
   vs candidate config
7. POST .../analyze: Change Engine queries the cohort (embedding + structured
   filters matching the agent + relevant workflows), samples it, replays the
   candidate config against each sampled input (deterministic mock by default,
   or a real model call plus a real LLM-judge call once the project has
   configured its own llm_provider/API key), computes metrics old vs new per
   segment, writes impact_report + impact_evidence
8. Dashboard renders the Blast Radius Diff and Ship/Modify/Block gate from
   the impact_report, with evidence links back to real trace pairs
9. Optionally: worst regressions become regression_tests; the change_proposal
   can be marked shipped, and once new post-ship traces accumulate, a
   prediction_outcome row compares predicted vs actual
```
