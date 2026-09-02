import Link from "next/link";
import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { CommandCenterData, CommandCenterProposal, Recommendation } from "@/lib/types";
import { Badge } from "@/components/badge";

const RISK_DOT: Record<Recommendation, string> = {
  SHIP: "bg-success",
  MODIFY: "bg-warning",
  BLOCK: "bg-danger",
  INSUFFICIENT_EVIDENCE: "bg-muted",
};

const RISK_LABEL: Record<Recommendation, string> = {
  SHIP: "Safe to ship",
  MODIFY: "Needs modification",
  BLOCK: "High risk",
  INSUFFICIENT_EVIDENCE: "Needs more evidence",
};

export default async function CommandCenterPage() {
  const res = await serverApiFetch("/v1/command-center");
  if (res.status === 401) redirect("/login");

  const data: CommandCenterData | null = res.ok ? await res.json() : null;
  const waiting = data?.waiting_for_review ?? [];
  const awaitingOutcome = data?.awaiting_outcome_verification ?? [];
  const calibration = data?.prediction_accuracy;

  const nothingNeedsAttention = waiting.length === 0 && awaitingOutcome.length === 0;

  return (
    <div className="p-8">
      <div className="animate-fade-in relative mb-10 overflow-hidden rounded-xl border border-border bg-surface px-6 py-8 sm:px-10">
        <div className="bg-grid bg-glow pointer-events-none absolute inset-0 opacity-[0.25]" />
        <div className="starfield" aria-hidden="true" />
        <div className="relative z-10 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-2 flex items-center gap-1.5 font-mono text-[10px] font-medium tracking-wider text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-success glow-pulse" />
              COMMAND CENTER
            </p>
            <h1 className="font-mono text-2xl text-foreground sm:text-3xl">What needs attention</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted">
              Not a metrics wall - changes waiting on a decision, the riskiest ones
              first, and shipped changes still waiting on real traffic to confirm
              what Kosma predicted.
            </p>
          </div>
          <Link
            href="/dashboard/propose"
            className="shrink-0 rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 active:scale-[0.98]"
          >
            + Propose a change
          </Link>
        </div>
      </div>

      {calibration && calibration.segments_evaluated > 0 && (
        <Link
          href="/dashboard/scorecard"
          className="feature-item mb-10 flex items-center justify-between rounded-lg border border-border bg-surface p-4 transition-all duration-200 ease-premium hover:-translate-y-0.5 hover:border-accent/40"
          style={{ "--fade-delay": "0s" } as React.CSSProperties}
        >
          <div>
            <p className="text-xs font-medium tracking-wider text-muted">PREDICTION ACCURACY</p>
            <p className="mt-1 text-sm text-foreground">
              {calibration.calibration_rate !== null
                ? `${(calibration.calibration_rate * 100).toFixed(0)}% of predicted directions matched reality`
                : "Not enough live data yet"}{" "}
              across {calibration.segments_evaluated} checked segments
            </p>
          </div>
          <span className="text-xs text-accent">View Scorecard →</span>
        </Link>
      )}

      {nothingNeedsAttention ? (
        <div className="feature-item rounded-lg border border-dashed border-border p-8 text-center">
          <p className="text-sm text-muted">
            Nothing needs attention right now. Propose a change to get started, or
            check{" "}
            <Link href="/dashboard/propose" className="text-accent hover:underline">
              recent activity
            </Link>
            .
          </p>
        </div>
      ) : (
        <>
          {waiting.length > 0 && (
            <Section title={`${waiting.length} CHANGE${waiting.length === 1 ? "" : "S"} WAITING FOR REVIEW`} delay={0.05}>
              <div className="space-y-2">
                {waiting.map((p) => (
                  <ProposalRow key={p.id} proposal={p} />
                ))}
              </div>
            </Section>
          )}

          {awaitingOutcome.length > 0 && (
            <Section
              title={`${awaitingOutcome.length} SHIPPED CHANGE${awaitingOutcome.length === 1 ? "" : "S"} AWAITING OUTCOME VERIFICATION`}
              delay={0.15}
            >
              <div className="space-y-2">
                {awaitingOutcome.map((p) => (
                  <ProposalRow key={p.id} proposal={p} showAwaiting />
                ))}
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

function Section({ title, children, delay = 0 }: { title: string; children: React.ReactNode; delay?: number }) {
  return (
    <div className="feature-item mb-10" style={{ "--fade-delay": `${delay}s` } as React.CSSProperties}>
      <p className="mb-3 text-xs font-medium tracking-wider text-muted">{title}</p>
      {children}
    </div>
  );
}

function ProposalRow({ proposal, showAwaiting }: { proposal: CommandCenterProposal; showAwaiting?: boolean }) {
  return (
    <Link
      href={`/dashboard/changes/${proposal.id}`}
      className="group flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3 transition-all duration-150 ease-premium hover:-translate-y-0.5 hover:border-accent/40"
    >
      <div className="flex items-center gap-3">
        {proposal.recommendation && (
          <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${RISK_DOT[proposal.recommendation]}`} />
        )}
        <div>
          <p className="text-sm text-foreground">{proposal.description ?? "Untitled change proposal"}</p>
          <p className="mt-0.5 text-xs text-muted">
            {proposal.agent_name ?? "Unknown agent"} · {formatRelativeTime(proposal.created_at)}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {showAwaiting ? (
          <Badge variant="neutral">awaiting live traffic</Badge>
        ) : proposal.recommendation ? (
          <Badge
            variant={
              proposal.recommendation === "BLOCK"
                ? "danger"
                : proposal.recommendation === "MODIFY"
                  ? "warning"
                  : proposal.recommendation === "SHIP"
                    ? "success"
                    : "neutral"
            }
          >
            {RISK_LABEL[proposal.recommendation]}
          </Badge>
        ) : null}
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
  );
}
