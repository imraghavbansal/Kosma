# TraceOS Database Schema (V1)

PostgreSQL + pgvector. All tables have `id` (uuid, pk) and `created_at` (timestamptz,
default now()) unless noted. Foreign keys cascade on delete for child rows of a project
(supports the "delete a project, confirm cascade" DoD item).

## ER overview (text)

```
organizations 1──* projects 1──* agents 1──* agent_configs
                       │                         │  ▲
                       │                         │  │ baseline/candidate
                       │                         │  │
                       *                         *  │
                    traces                 change_proposals 1──1 impact_reports
                    │  │  │                                          │
        spans ──────┘  │  └── retrieval_events            impact_evidence (*)
          │             │                                       │ → traces (baseline/replay)
    tool_calls   evaluations                              regression_tests
                       │
              failure_cluster_members * ── 1 failure_clusters

change_proposals 1──? prediction_outcomes
```

## Tables

### organizations
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| name | text | |
| created_at | timestamptz | |

Single seeded row for V1 (no signup flow). Kept so `project.organization_id` isn't a
schema change later.

### projects
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| organization_id | uuid fk → organizations | |
| name | text | |
| api_key_hash | text | sha256 of the ingestion API key, never store plaintext |
| created_at | timestamptz | |

### agents
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| project_id | uuid fk → projects | |
| name | text | e.g. "Refund Assistant" |
| description | text | |
| created_at | timestamptz | |

### agent_configs
Unifies "prompt version" and "model/config version" from the original specs.

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| agent_id | uuid fk → agents | |
| kind | enum(prompt, model) | which axis this config version changes |
| version_label | text | e.g. "v42", "gpt-x-2026-08" |
| prompt_text | text, nullable | set when kind=prompt |
| model_provider | text, nullable | set when kind=model (mock/openai/anthropic) |
| model_name | text, nullable | |
| temperature | float, nullable | |
| params | jsonb | other model/config params |
| is_baseline | boolean | current production config for the agent |
| created_at | timestamptz | |

### traces
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| project_id | uuid fk → projects | |
| agent_id | uuid fk → agents | |
| agent_config_id | uuid fk → agent_configs | which config produced this trace |
| trace_ref | text | external/display id, e.g. "8F31A" |
| workflow_tag | text | e.g. refund, order_status, account_change |
| segment_tags | jsonb | e.g. {"region": "international"} |
| input_text | text | |
| input_embedding | vector(1536) | pgvector column, nullable until worker processes it |
| status | enum(pending, completed, error) | |
| success | boolean, nullable | lightweight outcome heuristic |
| latency_ms | int | |
| input_tokens | int | |
| output_tokens | int | |
| total_tokens | int | |
| estimated_cost | numeric | derived from `model_pricing`, always labeled "estimated" |
| model_provider | text | |
| model_name | text | |
| source | enum(live, replay) | replay traces are produced by the Change Engine |
| created_at | timestamptz | |

Indexes: btree(project_id, agent_id, created_at), ivfflat(input_embedding) for cohort
similarity search, btree(workflow_tag).

### spans
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| trace_id | uuid fk → traces | |
| parent_span_id | uuid fk → spans, nullable | self-referencing hierarchy |
| span_type | enum(query_processing, retrieval, embedding, vector_search, reranking, llm, tool_call, citation_check, custom) | |
| name | text | |
| input | jsonb | |
| output | jsonb | |
| metadata | jsonb | |
| latency_ms | int | |
| error | text, nullable | |
| created_at | timestamptz | |

### tool_calls
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| span_id | uuid fk → spans | |
| tool_name | text | |
| arguments | jsonb | |
| result | jsonb | |
| valid_arguments | boolean | deterministic schema check |
| success | boolean | |
| created_at | timestamptz | |

### retrieval_events
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| span_id | uuid fk → spans | |
| query | text | |
| documents | jsonb | array of {doc_id, title, score, rerank_score, selected} |
| created_at | timestamptz | |

### evaluations
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| trace_id | uuid fk → traces | |
| metric_name | text | e.g. relevance, faithfulness, tool_selection |
| score | float | |
| reason | text | |
| evaluator_type | text | deterministic \| statistical \| llm |
| created_at | timestamptz | |

### failure_clusters
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| project_id | uuid fk → projects | |
| label | text | e.g. "Stale retrieval" |
| description | text | |
| trace_count | int | denormalized count, refreshed by worker |
| created_at | timestamptz | |

### failure_cluster_members
| column | type | notes |
|---|---|---|
| cluster_id | uuid fk → failure_clusters | |
| trace_id | uuid fk → traces | |
| (pk: cluster_id, trace_id) | | |

### change_proposals
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| project_id | uuid fk → projects | |
| agent_id | uuid fk → agents | |
| baseline_config_id | uuid fk → agent_configs | |
| candidate_config_id | uuid fk → agent_configs | |
| description | text | |
| status | enum(draft, analyzing, analyzed, shipped) | |
| shipped_at | timestamptz, nullable | |
| created_at | timestamptz | |

### impact_reports
One-to-one with an analyzed change_proposal.

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| change_proposal_id | uuid fk → change_proposals, unique | |
| cohort_size | int | total matched historical executions |
| sample_size | int | number actually replayed |
| recommendation | enum(SHIP, MODIFY, BLOCK) | |
| confidence | float | 0-1, calibrated from sample size + effect size, never asserted as certainty |
| overall_metrics | jsonb | {success_delta, latency_delta_ms, cost_delta, tool_accuracy_delta, groundedness_delta} |
| segment_metrics | jsonb | array of {segment, cohort_size, ...same metric shape} |
| created_at | timestamptz | |

### impact_evidence
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| impact_report_id | uuid fk → impact_reports | |
| segment | text, nullable | null = overall |
| baseline_trace_id | uuid fk → traces | |
| replay_trace_id | uuid fk → traces | source=replay |
| note | text | e.g. "tool selection flipped from valid to invalid" |
| created_at | timestamptz | |

### regression_tests
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| project_id | uuid fk → projects | |
| impact_report_id | uuid fk → impact_reports, nullable | |
| source_trace_id | uuid fk → traces | |
| input_text | text | |
| context_snapshot | jsonb | retrieved docs / tool state at capture time |
| expected_condition | text | human-readable, e.g. "must not call refund_tool with amount > order_total" |
| baseline_output | text | |
| status | enum(pending, passed, failed) | execution engine itself is V2; V1 stores pending |
| created_at | timestamptz | |

### prediction_outcomes
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| change_proposal_id | uuid fk → change_proposals, unique | |
| predicted_metrics | jsonb | copy of impact_report.overall_metrics at ship time |
| actual_metrics | jsonb | recomputed from real post-ship traces |
| prediction_error | jsonb | actual - predicted, per metric |
| evaluated_at | timestamptz | |

### model_pricing
| column | type | notes |
|---|---|---|
| id | uuid pk | |
| provider | text | |
| model_name | text | |
| input_price_per_1k | numeric | |
| output_price_per_1k | numeric | |
| currency | text | default "USD" |
| effective_date | date | |

Cost is always computed from this table, never hardcoded inline, and always surfaced as
"estimated cost."
