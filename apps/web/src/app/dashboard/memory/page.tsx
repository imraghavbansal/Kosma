import Link from "next/link";
import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import { Badge } from "@/components/badge";

interface MemoryItem {
  id: string;
  description: string | null;
  agent_name: string | null;
  status: string;
  created_at: string;
  recommendation: string | null;
  confidence: number | null;
  worst_segment: { segment: string; success_delta: number } | null;
  outcome_summary: { segments_confirmed: number; mean_absolute_error: number } | null;
}

export default async function BehavioralMemoryPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  const res = await serverApiFetch(`/v1/behavioral-memory${query}`);
  if (res.status === 401) redirect("/login");

  const data: { total: number; items: MemoryItem[] } = res.ok ? await res.json() : { total: 0, items: [] };

  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Behavioral Memory</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Every change Kosma has reviewed, searchable - has this workflow broken
        before, what was predicted, what actually happened. Real substring search
        over real rows, not a fabricated &quot;similar incident.&quot;
      </p>

      <form method="GET" className="mt-6 flex gap-2">
        <input
          type="text"
          name="q"
          defaultValue={q ?? ""}
          placeholder="Search by workflow, segment, agent, or description..."
          className="w-full max-w-md rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
        />
        <button
          type="submit"
          className="rounded-md border border-border bg-surface-2 px-4 py-2 text-sm font-medium text-foreground transition-all duration-150 ease-premium hover:bg-border"
        >
          Search
        </button>
        {q && (
          <Link
            href="/dashboard/memory"
            className="flex items-center px-2 text-xs text-muted transition-colors duration-150 hover:text-foreground"
          >
            Clear
          </Link>
        )}
      </form>

      <p className="mt-4 text-xs text-muted">
        {data.total} change{data.total === 1 ? "" : "s"}
        {q ? ` matching "${q}"` : " total"}
      </p>

      {data.items.length === 0 ? (
        <div className="mt-4 rounded-lg border border-dashed border-border p-8 text-center">
          <p className="text-sm text-muted">
            {q ? "No matching changes found." : "No changes reviewed yet."}
          </p>
        </div>
      ) : (
        <div className="mt-4 space-y-2">
          {data.items.map((item) => (
            <Link
              key={item.id}
              href={`/dashboard/changes/${item.id}`}
              className="group block rounded-lg border border-border bg-surface p-4 transition-all duration-150 ease-premium hover:-translate-y-0.5 hover:border-accent/40"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="truncate text-sm text-foreground">
                    {item.description ?? "Untitled change proposal"}
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    {item.agent_name ?? "Unknown agent"} · {item.status} ·{" "}
                    {formatRelativeTime(item.created_at)}
                  </p>
                  {item.worst_segment && (
                    <p className="mt-1.5 font-mono text-xs text-muted">
                      worst segment: {item.worst_segment.segment} (
                      {item.worst_segment.success_delta >= 0 ? "+" : ""}
                      {(item.worst_segment.success_delta * 100).toFixed(1)} pts)
                    </p>
                  )}
                  {item.outcome_summary && (
                    <p className="mt-1 text-xs text-muted">
                      confirmed against real traffic - avg error{" "}
                      {(item.outcome_summary.mean_absolute_error * 100).toFixed(1)} pts across{" "}
                      {item.outcome_summary.segments_confirmed} segment
                      {item.outcome_summary.segments_confirmed === 1 ? "" : "s"}
                    </p>
                  )}
                </div>
                {item.recommendation && (
                  <Badge
                    variant={
                      item.recommendation === "BLOCK"
                        ? "danger"
                        : item.recommendation === "MODIFY"
                          ? "warning"
                          : item.recommendation === "SHIP"
                            ? "success"
                            : "neutral"
                    }
                  >
                    {item.recommendation.replace("_", " ")}
                  </Badge>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
