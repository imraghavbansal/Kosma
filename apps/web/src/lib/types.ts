// Mirrors apps/api/kosma_api/schemas/ingestion.py - kept in sync by hand since V1
// has no shared-schema codegen step (see docs/development-plan.md Phase 10 for
// whether that's worth adding later).

export type TraceStatus = "pending" | "completed" | "error";
export type TraceSource = "live" | "replay";
export type SpanType =
  | "query_processing"
  | "retrieval"
  | "embedding"
  | "vector_search"
  | "reranking"
  | "llm"
  | "tool_call"
  | "citation_check"
  | "custom";

export interface TraceListItem {
  id: string;
  trace_ref: string;
  workflow_tag: string | null;
  status: TraceStatus;
  success: boolean | null;
  latency_ms: number;
  total_tokens: number;
  estimated_cost: number;
  created_at: string;
}

export interface TraceListResponse {
  items: TraceListItem[];
  total: number;
}

export interface ToolCallData {
  id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
  valid_arguments: boolean;
  success: boolean;
}

export interface RetrievalEventData {
  id: string;
  query: string;
  documents: Array<{
    doc_id: string;
    title?: string;
    score: number;
    rerank_score?: number;
    selected: boolean;
  }>;
}

export interface Span {
  id: string;
  parent_span_id: string | null;
  span_type: SpanType;
  name: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  metadata: Record<string, unknown>;
  latency_ms: number;
  error: string | null;
  created_at: string;
  tool_calls: ToolCallData[];
  retrieval_events: RetrievalEventData[];
}

export interface TraceDetail {
  id: string;
  trace_ref: string;
  agent_id: string;
  agent_config_id: string;
  workflow_tag: string | null;
  segment_tags: Record<string, string>;
  input_text: string;
  status: TraceStatus;
  success: boolean | null;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  model_provider: string | null;
  model_name: string | null;
  source: TraceSource;
  created_at: string;
  spans: Span[];
}
