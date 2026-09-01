# Kosma V1 Development Plan

Working style: implement one phase, run it, test it, report exactly what works and what
doesn't, pause for review before the next phase. No phase is claimed done without having
actually been run.

## Phase 0 - Planning (this document set)
Deliverables: PRODUCT-SPEC.md, docs/architecture.md, docs/database-schema.md,
docs/api-design.md, docs/development-plan.md.
DoD: reviewed and approved by you before any code is written.

## Phase 1 - Foundation
Build: monorepo scaffold, docker-compose (postgres+pgvector, redis, api, web), Alembic
migrations for the full V1 schema, shared-secret dashboard login, health check endpoints.
DoD: `docker compose up` boots all four services; empty dashboard loads and requires
login; `alembic upgrade head` creates every table in database-schema.md; `GET /v1/health`
returns 200 from a running container.

## Phase 2 - SDK + Ingestion
Build: `kosma` Python SDK (`trace()`/`span()`), `POST /v1/traces`, hashed API-key auth,
persistence of trace+spans+tool_calls+retrieval_events.
DoD: a standalone script using the SDK sends one real trace against a running API, and
`GET /v1/traces/{id}` returns it with correct span hierarchy. Unit tests for the SDK's
span-tree construction and the ingestion endpoint's auth/validation.

## Phase 3 - Demo Agent + Seed Corpus
Build: customer-support demo agent (workflows: refund, order_status, account_change;
segments: domestic/international) using MockProvider; two agent_configs - a baseline and
a candidate deliberately known to regress refund+international; seed script generating a
labeled historical corpus (thousands of traces) across both configs over simulated time.
DoD: seed script runs idempotently, populates the DB, every seeded trace is queryable and
visibly marked as demo data.

## Phase 4 - Trace Explorer & Evidence UI (secondary nav)
Build: trace list, trace detail with span timeline, tool-call and retrieval inspectors.
DoD: any seeded trace can be opened and its full execution inspected in the UI.

## Phase 5 - Embeddings & Cohort Matching
Build: Arq worker that embeds trace input text, assigns/validates workflow+segment tags,
a cohort-query function (agent + config + workflow/segment filters + embedding similarity
-> sampled trace set).
DoD: a direct test of the cohort function against the seeded corpus returns the expected
workflow/segment distribution, verified against known seed data, not assumed.

## Phase 6 - Change Engine
Build: change_proposals CRUD, `/analyze` job (cohort match -> counterfactual replay via
MockProvider -> segmented metric comparison -> impact_report + impact_evidence rows,
recommendation logic for SHIP/MODIFY/BLOCK with a documented confidence calibration).
DoD: analyzing the seeded "bad" candidate against baseline produces an impact_report that
correctly flags refund/international as regressed - verified by inspecting the actual
replayed trace pairs, not asserted.

## Phase 7 - Home Dashboard (Propose a Change)
Build: propose-change flow, Blast Radius Diff visualization, evidence drill-through to
real trace pairs, Ship/Modify/Block gate display. This becomes the dashboard's home
screen, replacing a generic trace list.
DoD: the full demo narrative (propose -> analyze -> see regression -> drill into
evidence) is walkable end-to-end in the browser.

## Phase 8 - Regression Suite Generation
Build: `POST /v1/impact-reports/{id}/regression-tests`, list/detail views.
DoD: the worst regressions from Phase 6's report become inspectable regression_tests rows
with their originating evidence.

## Phase 9 - Prediction Scorecard
Build: ship flow, simulated post-ship trace window, prediction_outcomes computation,
predicted-vs-actual UI.
DoD: at least one full predict -> ship -> measure loop closes with real seeded before/
after numbers (not fabricated).

## Phase 10 - Polish, Tests, Docs
Build: unit tests (cost calc, cohort matching, metric computation, impact report logic),
integration test (SDK -> API -> DB -> change engine -> dashboard), README with quick
start, limitations section, final demo script rehearsal.
DoD: test suite passes in CI-equivalent local run; README quick start works from a clean
clone; documented limitations match what was actually built.

## Phase 11 - Deployment
Build: live hosting so the product has a real URL, not just a local clone. Frontend on
Vercel, backend on a small always-on host (Railway/Render/Fly - picked when we get here),
database already hosted on Supabase. Auth stays exactly what it is: one shared secret
gates the dashboard (see "Deployment scope" decision, 2026-09-01) - no new auth system,
this is the same single-tenant model already built, just reachable from outside localhost.
DoD: the deployed URL runs the same verified flow as local - login, propose a change,
see the Blast Radius Diff - with nothing silently different from what passed locally.

## Minimum viable vertical slice
Phases 1-4: a real trace, sent by a real (mock-backed) agent through the real SDK, stored
and inspectable in the dashboard. Nothing about the change-intelligence engine is faked
before this slice works end to end.

## Explicitly out of scope for V1
OTLP ingestion, multi-user auth/RBAC, retrieval/tool-schema change types, trained ML
predictor, automated regression execution against live deployments, third-party
integrations (GitHub/Slack/Jira), alerting, autonomous fixes.
