import Link from "next/link";
import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { Agent, ChangeProposal } from "@/lib/types";
import { Badge } from "@/components/badge";
import { ProposeChangeForm } from "@/components/propose-change-form";

export default async function DashboardHome() {
  const [agentsRes, proposalsRes] = await Promise.all([
    serverApiFetch("/v1/agents"),
    serverApiFetch("/v1/change-proposals"),
  ]);

  if (agentsRes.status === 401 || proposalsRes.status === 401) redirect("/login");

  const agents: Agent[] = agentsRes.ok ? (await agentsRes.json()).items : [];
  const proposals: ChangeProposal[] = proposalsRes.ok ? (await proposalsRes.json()).items : [];

  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Propose a Change</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Pick a candidate config, run it against a matched historical cohort, and see
        exactly which workflows and segments it helps or breaks before you ship it.
      </p>

      <div className="mt-6">
        {agents.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border p-6">
            <p className="text-sm text-muted">
              No agents yet. Run the demo agent&apos;s seed script (
              <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">
                apps/demo-agent
              </code>
              ) to populate one.
            </p>
          </div>
        ) : (
          <ProposeChangeForm agents={agents} />
        )}
      </div>

      {proposals.length > 0 && (
        <div className="mt-10">
          <p className="mb-3 text-xs font-medium tracking-wider text-muted">RECENT CHANGE PROPOSALS</p>
          <div className="overflow-hidden rounded-lg border border-border">
            {proposals.map((p) => (
              <Link
                key={p.id}
                href={`/dashboard/changes/${p.id}`}
                className="flex items-center justify-between border-b border-border bg-surface px-4 py-3 transition-colors duration-150 last:border-0 hover:bg-surface-2"
              >
                <div>
                  <p className="text-sm text-foreground">{p.description ?? "Untitled change proposal"}</p>
                  <p className="mt-0.5 text-xs text-muted">{formatRelativeTime(p.created_at)}</p>
                </div>
                <StatusBadge status={p.status} />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "analyzed") return <Badge variant="success">analyzed</Badge>;
  if (status === "shipped") return <Badge variant="accent">shipped</Badge>;
  if (status === "analyzing") return <Badge variant="warning">analyzing</Badge>;
  return <Badge variant="neutral">draft</Badge>;
}
