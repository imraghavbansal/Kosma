"use client";

import { useState } from "react";
import type { Span } from "@/lib/types";
import { formatLatency } from "@/lib/format";
import { Badge } from "@/components/badge";

const SPAN_TYPE_COLOR: Record<string, string> = {
  retrieval: "bg-accent",
  vector_search: "bg-accent",
  embedding: "bg-accent",
  reranking: "bg-accent",
  llm: "bg-success",
  tool_call: "bg-warning",
  citation_check: "bg-warning",
  query_processing: "bg-muted",
  custom: "bg-muted",
};

function buildTree(spans: Span[]): Map<string | null, Span[]> {
  const byParent = new Map<string | null, Span[]>();
  for (const span of spans) {
    const key = span.parent_span_id;
    if (!byParent.has(key)) byParent.set(key, []);
    byParent.get(key)!.push(span);
  }
  return byParent;
}

export function SpanTimeline({ spans, traceLatencyMs }: { spans: Span[]; traceLatencyMs: number }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  if (spans.length === 0) {
    return <p className="text-sm text-muted">No spans recorded for this trace.</p>;
  }

  const tree = buildTree(spans);
  const maxLatency = Math.max(traceLatencyMs, ...spans.map((s) => s.latency_ms), 1);

  function renderLevel(parentId: string | null, depth: number): React.ReactNode {
    const children = tree.get(parentId) ?? [];
    return children.map((span) => (
      <div key={span.id}>
        <SpanRow
          span={span}
          depth={depth}
          maxLatency={maxLatency}
          expanded={expandedId === span.id}
          onToggle={() => setExpandedId(expandedId === span.id ? null : span.id)}
        />
        {renderLevel(span.id, depth + 1)}
      </div>
    ));
  }

  return <div className="rounded-lg border border-border bg-surface">{renderLevel(null, 0)}</div>;
}

function SpanRow({
  span,
  depth,
  maxLatency,
  expanded,
  onToggle,
}: {
  span: Span;
  depth: number;
  maxLatency: number;
  expanded: boolean;
  onToggle: () => void;
}) {
  const widthPct = Math.max((span.latency_ms / maxLatency) * 100, 2);
  const color = SPAN_TYPE_COLOR[span.span_type] ?? "bg-muted";

  return (
    <div className="border-b border-border last:border-0">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors duration-150 hover:bg-surface-2"
        style={{ paddingLeft: `${16 + depth * 20}px` }}
      >
        <span
          className={`shrink-0 text-muted transition-transform duration-200 ease-premium ${expanded ? "rotate-90" : ""}`}
        >
          ▸
        </span>
        <span className="w-40 shrink-0 truncate font-mono text-xs text-foreground">{span.name}</span>
        <span className="w-24 shrink-0 text-[10px] uppercase tracking-wide text-muted">
          {span.span_type.replace("_", " ")}
        </span>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-2">
          <div
            className={`h-full rounded-full ${color} transition-all duration-500 ease-premium`}
            style={{ width: `${widthPct}%` }}
          />
        </div>
        <span className="w-16 shrink-0 text-right font-mono text-xs text-muted">
          {formatLatency(span.latency_ms)}
        </span>
        {span.error && <Badge variant="danger">error</Badge>}
      </button>

      {expanded && (
        <div
          className="animate-fade-in space-y-3 border-t border-border bg-background/50 px-4 py-3"
          style={{ paddingLeft: `${32 + depth * 20}px` }}
        >
          {span.error && (
            <Field label="ERROR">
              <p className="text-sm text-danger">{span.error}</p>
            </Field>
          )}
          {Object.keys(span.input).length > 0 && (
            <Field label="INPUT">
              <Json value={span.input} />
            </Field>
          )}
          {Object.keys(span.output).length > 0 && (
            <Field label="OUTPUT">
              <Json value={span.output} />
            </Field>
          )}
          {span.tool_calls.map((tc) => (
            <Field key={tc.id} label={`TOOL CALL: ${tc.tool_name}`}>
              <div className="flex items-center gap-2 mb-1">
                <Badge variant={tc.success ? "success" : "danger"}>
                  {tc.success ? "success" : "failed"}
                </Badge>
                {!tc.valid_arguments && <Badge variant="warning">invalid arguments</Badge>}
              </div>
              <Json value={{ arguments: tc.arguments, result: tc.result }} />
            </Field>
          ))}
          {span.retrieval_events.map((re) => (
            <Field key={re.id} label="RETRIEVAL">
              <p className="mb-2 text-xs text-muted">Query: {re.query}</p>
              <div className="space-y-1.5">
                {re.documents.map((doc) => (
                  <div
                    key={doc.doc_id}
                    className={`flex items-center justify-between rounded-md border px-3 py-1.5 text-xs ${
                      doc.selected ? "border-success/30 bg-success/5" : "border-border bg-surface-2"
                    }`}
                  >
                    <span className="font-mono text-foreground">{doc.title ?? doc.doc_id}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-muted">score {doc.score.toFixed(2)}</span>
                      {doc.selected ? (
                        <Badge variant="success">selected</Badge>
                      ) : (
                        <Badge variant="neutral">rejected</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Field>
          ))}
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1 text-[10px] font-medium tracking-wider text-muted">{label}</p>
      {children}
    </div>
  );
}

function Json({ value }: { value: unknown }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-surface-2 p-2.5 font-mono text-xs text-foreground/90">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}
