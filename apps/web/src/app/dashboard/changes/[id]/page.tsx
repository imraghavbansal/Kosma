import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { ChangeProposal, ImpactReport, PredictionOutcome } from "@/lib/types";
import { Badge } from "@/components/badge";
import { BlastRadiusDiff } from "@/components/blast-radius-diff";
import { ShipGate } from "@/components/ship-gate";
import { AnalyzeButton } from "@/components/analyze-button";
import { GenerateRegressionSuiteButton, ShipButton } from "@/components/change-actions";
import { BackLink } from "@/components/back-link";
import { CountUp } from "@/components/count-up";

export default async function ChangeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const proposalRes = await serverApiFetch(`/v1/change-proposals/${id}`);
  if (proposalRes.status === 401) redirect("/login");
  if (proposalRes.status === 404) notFound();

  const proposal: ChangeProposal = await proposalRes.json();
  const reportRes = await serverApiFetch(`/v1/change-proposals/${id}/impact-report`);
  const report: ImpactReport | null = reportRes.ok ? await reportRes.json() : null;

  let outcome: PredictionOutcome | null = null;
  if (proposal.status === "shipped") {
    const outcomeRes = await serverApiFetch(`/v1/change-proposals/${id}/prediction-outcome`);
    outcome = outcomeRes.ok ? await outcomeRes.json() : null;
  }

  return (
    <div className="p-8">
      <BackLink href="/dashboard" label="Propose a Change" />
      <div className="mb-1 flex items-center gap-3">
        <h1 className="font-mono text-lg text-foreground">CHANGE PROPOSAL</h1>
        <Badge variant={proposal.status === "shipped" ? "accent" : proposal.status === "analyzed" ? "success" : "neutral"}>
          {proposal.status}
        </Badge>
      </div>
      <p className="mb-1 text-sm text-foreground">{proposal.description ?? "No description"}</p>
      <p className="mb-6 text-xs text-muted">{formatRelativeTime(proposal.created_at)}</p>

      {!report ? (
        <div className="rounded-lg border border-dashed border-border p-6">
          <p className="mb-3 text-sm text-muted">Not analyzed yet.</p>
          <AnalyzeButton proposalId={proposal.id} />
        </div>
      ) : (
        <div className="space-y-8">
          <ShipGate recommendation={report.recommendation} confidence={report.confidence} />

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Metric label="Cohort" value={<CountUp value={report.cohort_size} />} />
            <Metric label="Replayed" value={<CountUp value={report.sample_size} />} />
            <Metric
              label="Overall success"
              value={`${report.overall_metrics.success_delta >= 0 ? "+" : ""}${(
                report.overall_metrics.success_delta * 100
              ).toFixed(1)} pts`}
            />
            <Metric
              label="Avg tokens"
              value={`${(report.overall_metrics.token_delta_pct * 100).toFixed(0)}%`}
            />
          </div>

          <div>
            <p className="mb-3 text-xs font-medium tracking-wider text-muted">
              BLAST RADIUS DIFF - BY WORKFLOW / SEGMENT
            </p>
            <div className="rounded-lg border border-border bg-surface p-5">
              <BlastRadiusDiff segments={report.segment_metrics} />
            </div>
          </div>

          <div>
            <p className="mb-3 text-xs font-medium tracking-wider text-muted">
              EVIDENCE - BASELINE VS REPLAY TRACE PAIRS
            </p>
            <div className="overflow-hidden rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-surface-2 text-left text-xs text-muted">
                    <th className="px-4 py-2 font-medium">Segment</th>
                    <th className="px-4 py-2 font-medium">Baseline trace</th>
                    <th className="px-4 py-2 font-medium">Replay trace</th>
                    <th className="px-4 py-2 font-medium">Note</th>
                  </tr>
                </thead>
                <tbody>
                  {report.evidence.slice(0, 30).map((e) => (
                    <tr key={e.id} className="border-b border-border last:border-0 hover:bg-surface-2">
                      <td className="px-4 py-2 text-xs text-foreground/80">{e.segment}</td>
                      <td className="px-4 py-2">
                        <Link
                          href={`/dashboard/traces/${e.baseline_trace_id}`}
                          className="font-mono text-xs text-accent hover:underline"
                        >
                          {e.baseline_trace_id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="px-4 py-2">
                        <Link
                          href={`/dashboard/traces/${e.replay_trace_id}`}
                          className="font-mono text-xs text-accent hover:underline"
                        >
                          {e.replay_trace_id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="px-4 py-2 text-xs text-danger">{e.note ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {report.evidence.length > 30 && (
              <p className="mt-2 text-xs text-muted">
                Showing 30 of {report.evidence.length} replayed pairs.
              </p>
            )}
          </div>

          <div className="flex items-center gap-3 border-t border-border pt-6">
            <GenerateRegressionSuiteButton impactReportId={report.id} />
            {proposal.status !== "shipped" && <ShipButton proposalId={proposal.id} />}
          </div>

          {proposal.status === "shipped" && (
            <div>
              <p className="mb-3 text-xs font-medium tracking-wider text-muted">
                PREDICTION SCORECARD - PREDICTED VS ACTUAL
              </p>
              {!outcome || Object.keys(outcome.actual_metrics).length === 0 ? (
                <p className="text-sm text-muted">No comparison data yet.</p>
              ) : (
                <div className="space-y-2 rounded-lg border border-border bg-surface p-5">
                  {Object.entries(outcome.actual_metrics).map(([segment, actual]) => {
                    const predicted = outcome.predicted_metrics[segment];
                    return (
                      <div
                        key={segment}
                        className="flex items-center justify-between border-b border-border py-2 text-xs last:border-0"
                      >
                        <span className="font-mono text-foreground">{segment}</span>
                        {actual.status === "insufficient_data" ? (
                          <Badge variant="neutral">
                            insufficient live data ({actual.sample_size})
                          </Badge>
                        ) : (
                          <span className="text-muted">
                            predicted {(predicted.candidate_success_rate * 100).toFixed(0)}% - actual{" "}
                            {((actual.actual_success_rate ?? 0) * 100).toFixed(0)}% (n=
                            {actual.sample_size})
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-3 transition-all duration-200 ease-premium hover:-translate-y-0.5 hover:border-border-strong hover:shadow-sm">
      <p className="text-[10px] font-medium tracking-wider text-muted">{label.toUpperCase()}</p>
      <p className="mt-1 font-mono text-sm text-foreground">{value}</p>
    </div>
  );
}
