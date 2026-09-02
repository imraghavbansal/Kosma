import { notFound, redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatCost, formatLatency, formatRelativeTime, formatTokens } from "@/lib/format";
import type { TraceDetail } from "@/lib/types";
import { Badge } from "@/components/badge";
import { SpanTimeline } from "@/components/span-timeline";
import { BackLink } from "@/components/back-link";

export default async function TraceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const res = await serverApiFetch(`/v1/traces/${id}`);
  if (res.status === 401) redirect("/login");
  if (res.status === 404) notFound();
  if (!res.ok) {
    return (
      <div className="p-8">
        <p className="text-sm text-danger">Could not load trace (HTTP {res.status}).</p>
      </div>
    );
  }

  const trace: TraceDetail = await res.json();

  return (
    <div className="p-8">
      <BackLink href="/dashboard/traces" label="Traces" />
      <div className="mb-1 flex items-center gap-3">
        <h1 className="font-mono text-lg text-foreground">TRACE #{trace.trace_ref.slice(0, 8)}</h1>
        <Badge
          variant={
            trace.status === "error" || trace.success === false
              ? "danger"
              : trace.success === true
                ? "success"
                : "neutral"
          }
        >
          {trace.status === "error" ? "error" : trace.success === false ? "failed" : trace.status}
        </Badge>
        {trace.source === "replay" && <Badge variant="accent">replay</Badge>}
      </div>
      <p className="mb-6 text-xs text-muted">{formatRelativeTime(trace.created_at)}</p>

      <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
        <Metric label="Duration" value={formatLatency(trace.latency_ms)} />
        <Metric label="Tokens" value={formatTokens(trace.total_tokens)} />
        <Metric label="Cost" value={formatCost(trace.estimated_cost)} />
        <Metric label="Workflow" value={trace.workflow_tag?.replace("_", " ") ?? "n/a"} />
        <Metric label="Model" value={trace.model_name ?? "n/a"} />
        <Metric
          label="Segment"
          value={Object.entries(trace.segment_tags)[0]?.[1] ?? "n/a"}
        />
      </div>

      <div className="mb-8 rounded-lg border border-border bg-surface p-4">
        <p className="mb-1 text-xs font-medium text-muted">INPUT</p>
        <p className="text-sm text-foreground">{trace.input_text}</p>
      </div>

      <div>
        <p className="mb-3 text-xs font-medium tracking-wider text-muted">EXECUTION TIMELINE</p>
        <SpanTimeline spans={trace.spans} traceLatencyMs={trace.latency_ms} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-3 transition-colors duration-150 hover:border-border-strong">
      <p className="text-[10px] font-medium tracking-wider text-muted">{label.toUpperCase()}</p>
      <p className="mt-1 truncate font-mono text-sm text-foreground" title={value}>
        {value}
      </p>
    </div>
  );
}
