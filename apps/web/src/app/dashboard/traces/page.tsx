import Link from "next/link";
import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatCost, formatLatency, formatRelativeTime, formatTokens } from "@/lib/format";
import type { TraceListResponse } from "@/lib/types";
import { Badge } from "@/components/badge";

const WORKFLOWS = ["refund", "order_status", "account_change"];
const PAGE_SIZE = 50;

function statusVariant(status: string, success: boolean | null) {
  if (status === "error") return "danger" as const;
  if (success === false) return "danger" as const;
  if (success === true) return "success" as const;
  return "neutral" as const;
}

export default async function TracesPage({
  searchParams,
}: {
  searchParams: Promise<{ workflow?: string; offset?: string }>;
}) {
  const params = await searchParams;
  const workflow = params.workflow;
  const offset = Number(params.offset ?? "0") || 0;

  const query = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
  if (workflow) query.set("workflow_tag", workflow);

  const res = await serverApiFetch(`/v1/traces?${query.toString()}`);
  if (res.status === 401) redirect("/login");
  if (!res.ok) {
    return (
      <div className="p-8">
        <h1 className="font-mono text-xl text-foreground">Traces</h1>
        <p className="mt-4 text-sm text-danger">
          Could not load traces (HTTP {res.status}). Is the API running?
        </p>
      </div>
    );
  }

  const data: TraceListResponse = await res.json();

  return (
    <div className="p-8">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="font-mono text-xl text-foreground">Traces</h1>
          <p className="mt-1 text-sm text-muted">
            Evidence, not the home screen - {data.total.toLocaleString()} traces total.
          </p>
        </div>
      </div>

      <div className="mb-4 flex gap-2">
        <FilterPill label="All" href="/dashboard/traces" active={!workflow} />
        {WORKFLOWS.map((w) => (
          <FilterPill
            key={w}
            label={w.replace("_", " ")}
            href={`/dashboard/traces?workflow=${w}`}
            active={workflow === w}
          />
        ))}
      </div>

      {data.items.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-left text-xs text-muted">
                <th className="px-4 py-2.5 font-medium">Trace</th>
                <th className="px-4 py-2.5 font-medium">Workflow</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Latency</th>
                <th className="px-4 py-2.5 font-medium">Tokens</th>
                <th className="px-4 py-2.5 font-medium">Cost</th>
                <th className="px-4 py-2.5 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((trace) => (
                <tr key={trace.id} className="group border-b border-border last:border-0">
                  <td className="p-0">
                    <Link
                      href={`/dashboard/traces/${trace.id}`}
                      className="block px-4 py-2.5 font-mono text-xs text-foreground transition-colors duration-150 group-hover:bg-surface-2"
                    >
                      {trace.trace_ref.slice(0, 12)}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5 text-foreground/80">
                    {trace.workflow_tag?.replace("_", " ") ?? "n/a"}
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge variant={statusVariant(trace.status, trace.success)}>
                      {trace.status === "error" ? "error" : trace.success === false ? "failed" : trace.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-foreground/80">
                    {formatLatency(trace.latency_ms)}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-foreground/80">
                    {formatTokens(trace.total_tokens)}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-foreground/80">
                    {formatCost(trace.estimated_cost)}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted">{formatRelativeTime(trace.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination total={data.total} offset={offset} pageSize={PAGE_SIZE} workflow={workflow} />
    </div>
  );
}

function FilterPill({ label, href, active }: { label: string; href: string; active: boolean }) {
  return (
    <Link
      href={href}
      className={`rounded-full px-3 py-1 text-xs font-medium capitalize transition-all duration-150 ease-premium ${
        active
          ? "bg-accent text-accent-foreground"
          : "bg-surface-2 text-muted hover:bg-border hover:text-foreground"
      }`}
    >
      {label}
    </Link>
  );
}

function Pagination({
  total,
  offset,
  pageSize,
  workflow,
}: {
  total: number;
  offset: number;
  pageSize: number;
  workflow?: string;
}) {
  if (total <= pageSize) return null;
  const base = workflow ? `/dashboard/traces?workflow=${workflow}&` : "/dashboard/traces?";
  const hasPrev = offset > 0;
  const hasNext = offset + pageSize < total;
  return (
    <div className="mt-4 flex items-center justify-between text-xs text-muted">
      <span>
        {offset + 1}-{Math.min(offset + pageSize, total)} of {total.toLocaleString()}
      </span>
      <div className="flex gap-2">
        <Link
          href={`${base}offset=${Math.max(0, offset - pageSize)}`}
          aria-disabled={!hasPrev}
          className={`rounded-md px-2.5 py-1 transition-colors duration-150 ${
            hasPrev ? "bg-surface-2 hover:bg-border" : "pointer-events-none opacity-40"
          }`}
        >
          Previous
        </Link>
        <Link
          href={`${base}offset=${offset + pageSize}`}
          aria-disabled={!hasNext}
          className={`rounded-md px-2.5 py-1 transition-colors duration-150 ${
            hasNext ? "bg-surface-2 hover:bg-border" : "pointer-events-none opacity-40"
          }`}
        >
          Next
        </Link>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border p-10 text-center">
      <p className="text-sm text-muted">
        No traces yet. Send one with the Kosma SDK, or run the demo agent&apos;s seed script
        (<code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">apps/demo-agent</code>).
      </p>
    </div>
  );
}
