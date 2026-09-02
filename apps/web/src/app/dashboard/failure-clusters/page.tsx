import Link from "next/link";
import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { Badge } from "@/components/badge";

interface Cluster {
  label: string;
  workflow: string;
  region: string;
  count: number;
  sample_trace_ids: string[];
}

export default async function FailureClustersPage() {
  const res = await serverApiFetch("/v1/analytics/failure-clusters");
  if (res.status === 401) redirect("/login");

  const data: { clusters: Cluster[]; total_failures: number } = res.ok
    ? await res.json()
    : { clusters: [], total_failures: 0 };

  const maxCount = Math.max(...data.clusters.map((c) => c.count), 1);

  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Failure Clusters</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        {data.total_failures.toLocaleString()} failed traces, grouped by workflow and
        segment - real data, aggregated on demand, not a placeholder.
      </p>

      {data.clusters.length === 0 ? (
        <div className="mt-6 rounded-lg border border-dashed border-border p-6">
          <p className="text-sm text-muted">No failures recorded yet.</p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {data.clusters.map((cluster, i) => (
            <div
              key={cluster.label}
              className="animate-fade-in rounded-lg border border-border bg-surface p-4 transition-colors duration-150 hover:border-border-strong"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-foreground">
                    {cluster.workflow.replace("_", " ")}
                  </span>
                  <Badge variant="neutral">{cluster.region}</Badge>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted">{cluster.count} traces</span>
                  <Link
                    href={`/dashboard/traces?workflow=${cluster.workflow}`}
                    className="text-xs text-accent transition-colors duration-150 hover:underline"
                  >
                    View traces
                  </Link>
                </div>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
                <div
                  className="grow-bar h-full rounded-full bg-danger/70"
                  style={{ width: `${(cluster.count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
