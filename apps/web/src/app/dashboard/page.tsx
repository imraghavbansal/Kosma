import Link from "next/link";
import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { Agent, ChangeProposal } from "@/lib/types";
import { Badge } from "@/components/badge";
import { ProposeChangeForm } from "@/components/propose-change-form";
import { CountUp } from "@/components/count-up";
import { GitHubActivity } from "@/components/github-activity";

export default async function DashboardHome() {
  const [agentsRes, proposalsRes, tracesRes] = await Promise.all([
    serverApiFetch("/v1/agents"),
    serverApiFetch("/v1/change-proposals"),
    serverApiFetch("/v1/traces?limit=1"),
  ]);

  if (agentsRes.status === 401 || proposalsRes.status === 401) redirect("/login");

  const agents: Agent[] = agentsRes.ok ? (await agentsRes.json()).items : [];
  const proposals: ChangeProposal[] = proposalsRes.ok ? (await proposalsRes.json()).items : [];
  const totalTraces: number = tracesRes.ok ? (await tracesRes.json()).total : 0;

  const analyzedCount = proposals.filter((p) => p.status === "analyzed" || p.status === "shipped").length;
  const shippedCount = proposals.filter((p) => p.status === "shipped").length;

  return (
    <div className="p-8">
      <div className="animate-fade-in relative mb-10 overflow-hidden rounded-xl border border-border bg-surface px-6 py-8 sm:px-10">
        <div className="bg-grid bg-glow pointer-events-none absolute inset-0 opacity-[0.25]" />
        <div className="relative z-10">
          <p className="mb-2 flex items-center gap-1.5 font-mono text-[10px] font-medium tracking-wider text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-success glow-pulse" />
            LIVE · CHANGE INTELLIGENCE
          </p>
          <h1 className="font-mono text-2xl text-foreground sm:text-3xl">Propose a Change</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Pick a candidate config, run it against a matched historical cohort, and see
            exactly which workflows and segments it helps or breaks before you ship it.
          </p>
        </div>
      </div>

      <div className="mb-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <OverviewStat label="Agents" value={agents.length} delay={0} />
        <OverviewStat label="Traces" value={totalTraces} delay={0.05} />
        <OverviewStat label="Changes analyzed" value={analyzedCount} delay={0.1} />
        <OverviewStat label="Shipped" value={shippedCount} delay={0.15} />
      </div>

      <GitHubActivity />

      <Section title="PROPOSE" delay={0.2}>
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
      </Section>

      {proposals.length > 0 && (
        <Section title="RECENT CHANGE PROPOSALS" delay={0.3}>
          <div className="overflow-hidden rounded-lg border border-border">
            {proposals.map((p, i) => (
              <Link
                key={p.id}
                href={`/dashboard/changes/${p.id}`}
                className="group flex items-center justify-between border-b border-border bg-surface px-4 py-3 transition-all duration-150 last:border-0 hover:bg-surface-2"
                style={{ animationDelay: `${0.3 + i * 0.05}s` }}
              >
                <div>
                  <p className="text-sm text-foreground">{p.description ?? "Untitled change proposal"}</p>
                  <p className="mt-0.5 text-xs text-muted">{formatRelativeTime(p.created_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={p.status} />
                  <svg
                    viewBox="0 0 16 16"
                    className="h-3 w-3 text-muted opacity-0 transition-all duration-150 ease-premium group-hover:translate-x-0.5 group-hover:opacity-100"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  >
                    <path d="M6 4l4 4-4 4" />
                  </svg>
                </div>
              </Link>
            ))}
          </div>
        </Section>
      )}

      <Section title="EXPLORE" delay={0.4}>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <QuickLink
            href="/dashboard/projects"
            title="Projects"
            desc="Link a real GitHub repo and see its actual activity"
          />
          <QuickLink
            href="/dashboard/traces"
            title="Trace Explorer"
            desc="Every recorded execution, filterable by workflow"
          />
          <QuickLink
            href="/dashboard/failure-clusters"
            title="Failure Clusters"
            desc="Failed traces, grouped by workflow and segment"
          />
          <QuickLink
            href="/dashboard/scorecard"
            title="Prediction Scorecard"
            desc="Kosma grading its own forecasts against reality"
          />
        </div>
      </Section>
    </div>
  );
}

function OverviewStat({ label, value, delay }: { label: string; value: number; delay: number }) {
  return (
    <div
      className="feature-item group relative overflow-hidden rounded-lg border border-border bg-surface p-4 transition-all duration-200 ease-premium hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-sm"
      style={{ "--fade-delay": `${delay}s` } as React.CSSProperties}
    >
      <div className="absolute inset-x-0 top-0 h-0.5 origin-left scale-x-0 bg-accent transition-transform duration-300 ease-premium group-hover:scale-x-100" />
      <p className="text-[10px] font-medium tracking-wider text-muted">{label.toUpperCase()}</p>
      <p className="mt-1 font-mono text-2xl text-foreground">
        <CountUp value={value} />
      </p>
    </div>
  );
}

function Section({
  title,
  delay,
  children,
}: {
  title: string;
  delay: number;
  children: React.ReactNode;
}) {
  return (
    <div className="feature-item mb-10" style={{ "--fade-delay": `${delay}s` } as React.CSSProperties}>
      <p className="mb-3 text-xs font-medium tracking-wider text-muted">{title}</p>
      {children}
    </div>
  );
}

function QuickLink({ href, title, desc }: { href: string; title: string; desc: string }) {
  return (
    <Link
      href={href}
      className="group rounded-lg border border-border bg-surface p-4 transition-all duration-200 ease-premium hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-sm"
    >
      <p className="text-sm font-medium text-foreground transition-colors group-hover:text-accent">
        {title}
      </p>
      <p className="mt-1 text-xs text-muted">{desc}</p>
    </Link>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "analyzed") return <Badge variant="success">analyzed</Badge>;
  if (status === "shipped") return <Badge variant="accent">shipped</Badge>;
  if (status === "analyzing") return <Badge variant="warning">analyzing</Badge>;
  return <Badge variant="neutral">draft</Badge>;
}
