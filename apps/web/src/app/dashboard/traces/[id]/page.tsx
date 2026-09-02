import { notFound, redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatCost, formatLatency, formatRelativeTime, formatTokens } from "@/lib/format";
import type { TraceDetail } from "@/lib/types";
import { Badge } from "@/components/badge";
import { SpanTimeline } from "@/components/span-timeline";
import { BackLink } from "@/components/back-link";
import { CountUp } from "@/components/count-up";

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
        <Metric label="Duration" value={<CountUp value={trace.latency_ms} format={(n) => formatLatency(Math.round(n))} />} />
        <Metric label="Tokens" value={<CountUp value={trace.total_tokens} format={(n) => formatTokens(Math.round(n))} />} />
        <Metric label="Cost" value={<CountUp value={trace.estimated_cost} format={(n) => formatCost(n)} />} />
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

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-3 transition-all duration-200 ease-premium hover:-translate-y-0.5 hover:border-border-strong hover:shadow-sm">
      <p className="text-[10px] font-medium tracking-wider text-muted">{label.toUpperCase()}</p>
      <p className="mt-1 truncate font-mono text-sm text-foreground">{value}</p>
    </div>
  );
}
