import Link from "next/link";
import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { ProjectSummary } from "@/lib/types";
import { Badge } from "@/components/badge";

export default async function ProjectsPage() {
  const res = await serverApiFetch("/v1/projects");
  if (res.status === 401) redirect("/login");

  const projects: ProjectSummary[] = res.ok ? (await res.json()).items : [];

  return (
    <div className="p-8">
      <div className="animate-fade-in mb-8">
        <h1 className="font-mono text-2xl text-foreground">Projects</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Each project is a real workspace: link it to a GitHub repo to see that
          repo&apos;s actual commits and PRs, next to Kosma&apos;s trace and change history
          for it.
        </p>
      </div>

      {projects.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-6">
          <p className="text-sm text-muted">No projects yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p, i) => (
            <Link
              key={p.id}
              href={`/dashboard/projects/${p.id}`}
              className="feature-item group rounded-lg border border-border bg-surface p-4 transition-all duration-200 ease-premium hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-sm"
              style={{ "--fade-delay": `${i * 0.05}s` } as React.CSSProperties}
            >
              <div className="mb-2 flex items-center justify-between">
                <p className="truncate text-sm font-medium text-foreground transition-colors group-hover:text-accent">
                  {p.name}
                </p>
                {p.github_repo ? (
                  <Badge variant="success">linked</Badge>
                ) : (
                  <Badge variant="neutral">no repo</Badge>
                )}
              </div>
              {p.github_repo ? (
                <p className="mb-3 truncate font-mono text-xs text-muted">{p.github_repo}</p>
              ) : (
                <p className="mb-3 text-xs text-muted">Not linked to a GitHub repo yet</p>
              )}
              <div className="flex items-center gap-4 text-[11px] text-muted">
                <span>{p.agent_count} agents</span>
                <span>{p.trace_count} traces</span>
                <span>{p.change_proposal_count} changes</span>
              </div>
              <p className="mt-2 text-[10px] text-muted">created {formatRelativeTime(p.created_at)}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
