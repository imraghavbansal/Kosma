# Kosma — the AI change review system

Know what your AI change will break before you ship it.

**Live**: https://kosma-ai.vercel.app

Traditional code review answers "what code changed?" Kosma answers "what
production behavior will change because of it?" You propose a change to a
prompt, model, or agent config, and instead of eyeballing a handful of test
cases and hoping for the best, Kosma finds comparable historical executions of
your agent, replays the candidate config against them, and hands you an
evidence-backed verdict, broken down by workflow and user segment: SHIP,
MODIFY, BLOCK, or — when the data genuinely doesn't support a call —
INSUFFICIENT EVIDENCE. Every verdict states its evidence tier (replayed vs.
predicted), its limitations, and a recommended next action; it never asserts
confidence it hasn't earned.

## The problem this solves

Every team building on top of an LLM ships prompt and model changes constantly,
and almost always the same way: edit the prompt, run it against a few examples
by hand, ship it, and find out from users (or from a support queue, or from a
Slack thread at 2am) whether anything broke. There is no step in that workflow
where you actually know, ahead of time, what a change does to real traffic.

The observability tools that already exist in this space, LangSmith, Langfuse,
Helicone, Arize and the rest, are all built to answer "what happened." They are
trace viewers. Extremely good ones in some cases. But none of them answer the
question that actually matters right before you hit deploy: what is this change
about to break, and for whom.

That is the specific gap Kosma is built to close. Not a place to browse traces
after the fact. A gate your change has to pass through, the same way a CI check
gates a pull request:

- **Blast Radius Diff.** One visual per proposed change, showing exactly which
  workflows and which user segments gain versus regress. Computed from real
  historical executions replayed against the candidate config, not guessed at
  or eyeballed from a sample of five.
- **Ship / Modify / Block gate.** The whole analysis collapses into one
  CI-shaped verdict: status, confidence, evidence. It reads like something a
  deploy pipeline asks permission from, not a dashboard someone has to
  remember to check.
- **Prediction Scorecard.** Every verdict Kosma gives gets graded against what
  actually happened once the change ships. Its own forecasting accuracy is
  visible and tracked over time, instead of being a black box you're asked to
  trust on faith.

## How it actually works, end to end

1. An agent (in V1, a seeded demo customer support agent) runs, using the
   Kosma Python SDK to wrap each request in a trace: query processing,
   retrieval, tool calls, LLM generation, all recorded as spans with timing,
   token counts, and the model config that produced them.
2. When the trace completes, the SDK POSTs the full payload to the ingestion
   API in one shot. No partial or streaming ingestion in V1, that would add
   complexity the core loop doesn't need yet.
3. The API validates the project's API key, writes the trace and its spans,
   tool calls, and retrieval events to Postgres, and kicks off a background
   task without making the request wait for it.
4. That background task embeds the trace's input text with pgvector, assigns
   workflow and segment tags if they weren't already explicit, and runs a
   handful of deterministic failure heuristics.
5. A developer opens the dashboard, registers a candidate agent config (a new
   prompt version, or a different model), and creates a change proposal that
   points at a baseline config and the candidate.
6. Hitting "analyze" kicks off the change engine: it queries for a cohort of
   historical traces that match the agent and the relevant workflows using
   embedding similarity plus structured filters, samples that cohort, and
   replays the candidate config against each sampled input.
7. It compares baseline versus replayed metrics per segment (success rate,
   latency, cost, tool accuracy, groundedness) and writes an impact report:
   a recommendation of SHIP, MODIFY, or BLOCK, a confidence score, and
   evidence rows linking straight back to the real trace pairs that drove the
   verdict.
8. The dashboard renders that as the Blast Radius Diff and the gate, with
   every claim clickable down to the actual before/after traces behind it.
9. Once a change actually ships, real post-ship traces accumulate, and a
   prediction outcome row compares what Kosma predicted against what really
   happened. That's the Prediction Scorecard.

## What Kosma is not

Worth being direct about this, because it shapes every decision in the repo:

- It is not a generic trace viewer as its primary surface, even though tracing
  is the substrate everything else is built on.
- It is not OTLP-first. V1 ingestion is SDK-only. An OTLP collector is real
  work that doesn't move the actual thesis forward, so it's deliberately V2.
- It is not a trained ML forecasting product. V1's predictions are cohort
  statistics computed from real replayed executions, not a model trained on
  data that doesn't exist yet. A model trained on synthetic seed data would
  just be memorizing its own demo, which is worse than being honest about
  using statistics.
- It is not multi-tenant SaaS. Single-tenant, shared-secret auth, with the
  schema shaped so multi-tenancy is a later addition, not a rewrite.
- It is not an autonomous-fix or auto-PR system. It tells you what will break.
  It does not touch your prompt for you.

Full reasoning for every one of these calls, including the tradeoffs I
accepted, is in [PRODUCT-SPEC.md](PRODUCT-SPEC.md) and
[docs/architecture.md](docs/architecture.md).

## Status

**Live**: https://kosma-ai.vercel.app (frontend on Vercel, API on Render, DB on
Supabase - all free tier, no card required, no trial expiry - see
[docs/architecture.md](docs/architecture.md) for why Docker/Railway got
dropped along the way).

**The full core loop is built and verified against a real database**, not
toy data: propose a prompt/model change, Kosma finds the matched historical
cohort, replays the candidate config against it, produces a segmented Blast
Radius Diff and a SHIP / MODIFY / BLOCK / INSUFFICIENT-EVIDENCE verdict with
its evidence basis and limitations stated, generates a regression suite from
the worst regressions, and - once shipped - grades its own prediction
against real live traffic under the new config. Every step has been run and
verified against a real Postgres instance and, since self-serve onboarding
shipped, against a real deployed backend end-to-end (create a project, get
a real API key, send a real trace with it, confirm it lands) - not just
passed a unit test in isolation.

Real, working today (not mocked, not "coming soon"):

- **Self-serve onboarding.** Create a project from the dashboard, get a real
  API key on the spot, and a copy-paste Python SDK / curl snippet to send
  your first real trace - verified end to end against production.
- **GitHub sign-in with real repo activity.** OAuth is a second, equally
  privileged login method (not per-user data isolation - see
  [docs/architecture.md](docs/architecture.md)); once signed in, a project
  can link to a real GitHub repo and show its actual recent commits and pull
  requests, fetched live from the GitHub API.
- **Evidence-first verdicts.** Every impact report states its evidence basis
  (replayed against historical traffic, not live traffic under the
  candidate), its limitations, and a recommended next action - and says
  INSUFFICIENT EVIDENCE outright rather than guessing when no segment
  cleared the minimum sample bar.
- **API key regeneration**, GitHub Actions keep-alive for the free-tier
  backend, dark-mode-only decorative polish that never blocks a real
  interaction.

45 backend tests passing (`apps/api/tests`) plus the SDK's own suite
(`packages/sdk/tests`), all against a real Postgres instance, no mocked DB.
Several real bugs were found and fixed along the way rather than papered
over - connection pool exhaustion, a cascade-delete ordering bug, request
idempotency under retry, IPv6-only DNS on the deploy host, a verdict that
silently defaulted to SHIP when there wasn't enough data to say anything -
see the commit history for each, and [docs/architecture.md](docs/architecture.md)'s
revision notes for the ones that changed a design decision.

| Phase | What | Status |
|---|---|---|
| 0 | Planning: spec, architecture, schema, API design, roadmap | Done |
| 1 | Foundation: monorepo, DB, auth, dashboard shell | Done |
| 2 | SDK + Ingestion | Done |
| 3 | Demo Agent + Seed Corpus | Done |
| 4 | Trace Explorer & Evidence UI | Done |
| 5 | Embeddings & Cohort Matching | Done |
| 6 | Change Engine | Done |
| 7 | Home Dashboard (Propose a Change) | Done |
| 8 | Regression Suite Generation | Done |
| 9 | Prediction Scorecard | Done |
| 10 | Polish, Tests, Docs | Ongoing |
| 11 | Deployment | Done |
| 12 | Self-serve onboarding, real GitHub integration, evidence-first verdicts | Ongoing |

Full phase breakdown and definition of done for each is in
[docs/development-plan.md](docs/development-plan.md).

Working style for this project: build one phase, run it, test it, write down
exactly what works and what doesn't, then move to the next one. No phase gets
marked done without having actually been run against a real database, not just
written and assumed correct.

## Tech stack, and why

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind | Server Components for the read-heavy pages, TanStack Query only where polling or caching an async job actually earns its keep |
| Backend | Python + FastAPI + SQLAlchemy + Alembic | Native async, Pydantic validation fits the trace/span payload shape well, automatic OpenAPI docs come for free |
| Database | Postgres + pgvector, hosted on Supabase | Cohort matching similarity search lives in the same store as the relational data, so a cohort query is one SQL statement joining an embedding distance against structured filters instead of federating two databases. Supabase ships pgvector pre-enabled, which sidesteps compiling it from source on native Windows Postgres (no official prebuilt binary) |
| Background jobs | In-process asyncio tasks | Originally speced as Arq plus Redis. Changed after Docker Desktop proved unreliable for local dev (a known Docker Desktop / WSL2 networking fault). V1's actual job volume is a few thousand demo traces processed by one operator, so an extra broker buys nothing that a plain background task doesn't already give |
| Auth | Shared dashboard secret or GitHub OAuth (both equally privileged), hashed per-project API key for ingestion | Single-tenant portfolio deployment. Schema keeps `organization_id` and `project_id` so this isn't a rewrite if multi-tenancy is ever needed |
| AI calls | Mock provider only | Deterministic, zero cost, clearly labeled as demo data. A real provider abstraction exists in the code but isn't exercised in V1 |

Full rationale for every decision, written as problem, options considered,
decision, reason, and the tradeoff I accepted, is in
[docs/architecture.md](docs/architecture.md).

## Database schema

17 tables. The short version of the relationships:

```text
organizations -> projects -> agents -> agent_configs
                    |                        ^  (baseline / candidate)
                    v                        |
                 traces  ------------  change_proposals -> impact_reports
                 /  |  \                                        |
            spans  |   retrieval_events                 impact_evidence
              |     |                                    (links back to
        tool_calls  evaluations                        baseline + replay
                    |                                       traces)
          failure_cluster_members -> failure_clusters

          change_proposals -> prediction_outcomes
```

Everything a change proposal produces (impact reports, evidence, regression
tests, prediction outcomes) is modeled as plain foreign keys against a
shallow tree, not a generic graph schema. V1's actual relationship graph
doesn't need one. Full column-level detail for all 17 tables is in
[docs/database-schema.md](docs/database-schema.md).

## API surface

Base path `/v1`, OpenAPI docs auto-generated by FastAPI at `/docs`. Two auth
schemes: a bearer project API key for ingestion, a session cookie (set by
logging in with `KOSMA_DASHBOARD_SECRET`) for everything else.

```text
POST /v1/traces                                   ingest a completed trace

POST /v1/projects                                 create a project, get a real API key (shown once)
GET  /v1/projects
GET  /v1/projects/{id}
PATCH /v1/projects/{id}                            link/unlink a github_repo ("owner/name")
POST /v1/projects/{id}/regenerate-key               invalidate the old key, issue a new one

GET  /v1/agents
GET  /v1/agents/{id}
GET  /v1/agents/{id}/configs
POST /v1/agents/{id}/configs                      register a prompt or model version

GET  /v1/traces?workflow_tag=&agent_id=&status=&source=&q=
GET  /v1/traces/{id}                              full span/tool/retrieval tree

GET  /v1/failure-clusters
GET  /v1/failure-clusters/{id}
GET  /v1/evaluations?trace_id=

POST /v1/change-proposals                         propose baseline vs candidate config
GET  /v1/change-proposals?agent_id=&status=
GET  /v1/change-proposals/{id}
POST /v1/change-proposals/{id}/analyze             cohort match, replay, evidence-first verdict
GET  /v1/change-proposals/{id}/impact-report        SHIP/MODIFY/BLOCK/INSUFFICIENT_EVIDENCE + evidence
POST /v1/change-proposals/{id}/ship
GET  /v1/change-proposals/{id}/prediction-outcome   predicted vs actual, once available

POST /v1/impact-reports/{id}/regression-tests       generate from worst regressions
GET  /v1/regression-tests?project_id=&status=
GET  /v1/regression-tests/{id}

GET  /v1/analytics/overview
GET  /v1/public/stats                              unauthenticated: real aggregate counts only

GET  /v1/github/repos                              the signed-in user's real repos
GET  /v1/github/activity                           real recent commits/PRs across those repos
GET  /v1/github/repos/{owner}/{repo}/activity        real commits/PRs for one linked repo

POST /v1/auth/login
POST /v1/auth/logout
GET  /v1/auth/me
GET  /v1/auth/github/login                         GitHub OAuth
GET  /v1/auth/github/callback
```

Full request and response shapes are in [docs/api-design.md](docs/api-design.md).

## Quick start (no Docker required)

Requires a free [Supabase](https://supabase.com) project (Postgres with
pgvector, hosted).

```bash
git clone https://github.com/imraghavbansal/Kosma.git
cd Kosma
cp .env.example .env
# edit .env: set DATABASE_URL to your Supabase connection string,
# and KOSMA_DASHBOARD_SECRET to whatever you want to log in with
```

Backend:

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate   # .venv/Scripts/activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn kosma_api.main:app --reload
```

Frontend, in a separate terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000 and sign in with `KOSMA_DASHBOARD_SECRET` from
your `.env`. The backend's auto-generated API docs are at
http://localhost:8000/docs.

### Optional: Docker

`infra/docker-compose.yml` containerizes the API and web processes if you'd
rather not run them natively. It still expects `DATABASE_URL` in `.env` to
point at Supabase, it does not run Postgres locally.

## Running the backend tests

```bash
cd apps/api
python -m pytest tests/ -v
```

## Repository layout

```text
apps/
  web/          Next.js dashboard
  api/          FastAPI backend: ingestion, change engine, query API
    kosma_api/
      ingestion/       POST /v1/traces, auth, payload validation
      change_engine/   cohort matching, replay, impact reports
      analytics/       overview, failure clusters, evaluations
      models/          SQLAlchemy models
      schemas/         Pydantic schemas
      background/      in-process background tasks
      db/              session, migrations entrypoint
    alembic/
    tests/
  demo-agent/   Seeded customer-support agent (Phase 3)
packages/
  sdk/          Kosma Python SDK, pip-installable (Phase 2)
infra/
  docker-compose.yml   optional containerized path
docs/
  architecture.md       every design decision, with tradeoffs
  database-schema.md    full column-level schema
  api-design.md          full request/response shapes
  development-plan.md    phase-by-phase build plan and definition of done
PRODUCT-SPEC.md          product thesis, scope decisions, what's cut and why
```

## Why this is worth building

The prompt-shipping-on-vibes problem is real and it is universal. Anyone who
has worked on a product with an LLM in the loop has lived through the
"we changed the prompt and now refunds are broken for international users
and nobody noticed for three days" version of this story. Existing tools
solve the half of the problem that comes after that: here's what happened,
here's the trace. Kosma is built for the half that actually prevents it:
here's what is about to happen, before you ship.

That's also why the three pieces (Blast Radius Diff, the Ship/Modify/Block
gate, and the Prediction Scorecard) aren't decoration. They're the parts of
the product that have to be true for the pitch to hold up: that Kosma can
show real evidence, that it collapses into a decision instead of a pile of
metrics, and that it's honest and self-correcting about its own accuracy
instead of asserting confidence it hasn't earned.
