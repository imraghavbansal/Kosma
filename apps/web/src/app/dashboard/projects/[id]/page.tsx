import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { ProjectDetail } from "@/lib/types";
import { Badge } from "@/components/badge";
import { BackLink } from "@/components/back-link";
import { LinkRepo } from "@/components/link-repo";
import { RepoActivityPanel } from "@/components/repo-activity-panel";

export default async function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const res = await serverApiFetch(`/v1/projects/${id}`);
  if (res.status === 401) redirect("/login");
  if (res.status === 404) notFound();
  if (!res.ok) notFound();

  const project: ProjectDetail = await res.json();

  return (
    <div className="p-8">
      <BackLink href="/dashboard/projects" label="Projects" />

      <div className="animate-fade-in mb-8 mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-mono text-2xl text-foreground">{project.name}</h1>
          <p className="mt-1 text-xs text-muted">created {formatRelativeTime(project.created_at)}</p>
        </div>
        <LinkRepo projectId={project.id} currentRepo={project.github_repo} />
      </div>

      <div className="mb-10 grid grid-cols-3 gap-3">
        <StatCard label="Agents" value={project.agents.length} />
        <StatCard label="Traces" value={project.trace_count} />
        <StatCard label="Change proposals" value={project.change_proposals.length} />
      </div>

      <div className="mb-10">
        <p className="mb-3 text-xs font-medium tracking-wider text-muted">GITHUB REPO</p>
        {project.github_repo ? (
          <RepoActivityPanel repo={project.github_repo} />
        ) : (
          <div className="rounded-lg border border-dashed border-border p-5 text-sm text-muted">
            Not linked yet - link a repo above to see its real commits and pull requests
            here.
          </div>
        )}
      </div>

      <div className="mb-10">
        <p className="mb-3 text-xs font-medium tracking-wider text-muted">CHANGE PROPOSALS</p>
        {project.change_proposals.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border p-5 text-sm text-muted">
            No change proposals for this project yet - propose one from an agent below.
          </div>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border">
            {project.change_proposals.map((p) => (
              <Link
                key={p.id}
                href={`/dashboard/changes/${p.id}`}
                className="group flex items-center justify-between border-b border-border bg-surface px-4 py-3 transition-all duration-150 last:border-0 hover:bg-surface-2"
              >
                <div>
                  <p className="text-sm text-foreground">{p.description ?? "Untitled change proposal"}</p>
                  <p className="mt-0.5 text-xs text-muted">{formatRelativeTime(p.created_at)}</p>
                </div>
                <StatusBadge status={p.status} />
              </Link>
            ))}
          </div>
        )}
      </div>

      <div>
        <p className="mb-3 text-xs font-medium tracking-wider text-muted">AGENTS</p>
        {project.agents.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border p-5 text-sm text-muted">
            No agents yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {project.agents.map((a) => (
              <div key={a.id} className="rounded-lg border border-border bg-surface p-4">
                <p className="font-mono text-sm text-foreground">{a.name}</p>
                <p className="mt-1 text-xs text-muted">{a.configs.length} configs</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-[10px] font-medium tracking-wider text-muted">{label.toUpperCase()}</p>
      <p className="mt-1 font-mono text-xl text-foreground">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "analyzed") return <Badge variant="success">analyzed</Badge>;
  if (status === "shipped") return <Badge variant="accent">shipped</Badge>;
  if (status === "analyzing") return <Badge variant="warning">analyzing</Badge>;
  return <Badge variant="neutral">draft</Badge>;
}
