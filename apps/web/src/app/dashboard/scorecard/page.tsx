import Link from "next/link";
import { redirect } from "next/navigation";
import { serverApiFetch } from "@/lib/api-server";
import { formatRelativeTime } from "@/lib/format";
import type { CalibrationSummary, ChangeProposal, PredictionOutcome } from "@/lib/types";
import { Badge } from "@/components/badge";
import { CountUp } from "@/components/count-up";

export default async function ScorecardPage() {
  const [res, calibrationRes] = await Promise.all([
    serverApiFetch("/v1/change-proposals"),
    serverApiFetch("/v1/scorecard/calibration"),
  ]);
  if (res.status === 401) redirect("/login");

  const allProposals: ChangeProposal[] = res.ok ? (await res.json()).items : [];
  const shipped = allProposals.filter((p) => p.status === "shipped");
  const calibration: CalibrationSummary | null = calibrationRes.ok ? await calibrationRes.json() : null;

  const outcomes = await Promise.all(
    shipped.map(async (p) => {
      const r = await serverApiFetch(`/v1/change-proposals/${p.id}/prediction-outcome`);
      return r.ok ? ((await r.json()) as PredictionOutcome) : null;
    })
  );

  return (
    <div className="p-8">
      <h1 className="font-mono text-xl text-foreground">Prediction Scorecard</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        Every shipped change, graded against what real traffic under the new config
        actually did. This is Kosma checking its own work, not just yours.
      </p>

      {calibration && (
        <div className="animate-fade-in mt-6 rounded-lg border border-border bg-surface p-5">
          <p className="mb-3 text-xs font-medium tracking-wider text-muted">
            HOW MUCH SHOULD YOU TRUST KOSMA
          </p>
          {calibration.segments_evaluated === 0 ? (
            <p className="text-sm text-muted">
              No predictions have been checked against real live traffic yet - this
              fills in once a shipped change accumulates at least 3 live traces under
              its candidate config.
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <CalibrationStat
                label="Calibration rate"
                value={
                  calibration.calibration_rate !== null
                    ? `${(calibration.calibration_rate * 100).toFixed(0)}%`
                    : "n/a"
                }
                hint="predicted direction matched reality"
              />
              <CalibrationStat
                label="Segments checked"
                value={<CountUp value={calibration.segments_evaluated} />}
                hint="against real live traffic"
              />
              <CalibrationStat
                label="False positives"
                value={<CountUp value={calibration.false_positive_count} />}
                hint="predicted regression, wasn't one"
              />
              <CalibrationStat
                label="False negatives"
                value={<CountUp value={calibration.false_negative_count} />}
                hint="missed a real regression"
              />
            </div>
          )}
        </div>
      )}

      {shipped.length === 0 ? (
        <div className="mt-6 rounded-lg border border-dashed border-border p-6">
          <p className="text-sm text-muted">
            No shipped changes yet. Analyze a change proposal and ship it to start
            closing the loop.
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {shipped.map((proposal, i) => {
            const outcome = outcomes[i];
            return (
              <Link
                key={proposal.id}
                href={`/dashboard/changes/${proposal.id}`}
                className="block rounded-lg border border-border bg-surface p-5 transition-colors duration-150 hover:bg-surface-2"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-foreground">
                      {proposal.description ?? "Untitled change proposal"}
                    </p>
                    <p className="mt-1 text-xs text-muted">
                      Shipped {proposal.shipped_at ? formatRelativeTime(proposal.shipped_at) : ""}
                    </p>
                  </div>
                  {outcome ? (
                    <ScorecardSummary outcome={outcome} />
                  ) : (
                    <Badge variant="neutral">not evaluated</Badge>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

function CalibrationStat({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint: string;
}) {
  return (
    <div className="rounded-md border border-border bg-background p-3">
      <p className="text-[10px] font-medium tracking-wider text-muted">{label.toUpperCase()}</p>
      <p className="mt-1 font-mono text-lg text-foreground">{value}</p>
      <p className="mt-0.5 text-[10px] text-muted">{hint}</p>
    </div>
  );
}

function ScorecardSummary({ outcome }: { outcome: PredictionOutcome }) {
  const errors = Object.values(outcome.prediction_error);
  if (errors.length === 0) {
    return <Badge variant="neutral">awaiting live traffic</Badge>;
  }
  const avgAbsError = errors.reduce((sum, e) => sum + Math.abs(e), 0) / errors.length;
  const variant = avgAbsError < 0.1 ? "success" : avgAbsError < 0.2 ? "warning" : "danger";
  return (
    <div className="text-right">
      <p className="text-[10px] font-medium tracking-wider text-muted">AVG PREDICTION ERROR</p>
      <Badge variant={variant}>{(avgAbsError * 100).toFixed(1)} pts</Badge>
    </div>
  );
}
