import type { Recommendation } from "@/lib/types";

const GATE_STYLE: Record<Recommendation, { bg: string; border: string; text: string; label: string }> = {
  SHIP: { bg: "bg-success/10", border: "border-success/30", text: "text-success", label: "SHIP" },
  MODIFY: { bg: "bg-warning/10", border: "border-warning/30", text: "text-warning", label: "MODIFY" },
  BLOCK: { bg: "bg-danger/10", border: "border-danger/30", text: "text-danger", label: "BLOCK" },
};

export function ShipGate({ recommendation, confidence }: { recommendation: Recommendation; confidence: number }) {
  const style = GATE_STYLE[recommendation];
  return (
    <div className={`animate-fade-in rounded-lg border ${style.border} ${style.bg} p-5`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-medium tracking-wider text-muted">RECOMMENDATION</p>
          <p className={`mt-1 font-mono text-2xl font-bold ${style.text}`}>{style.label}</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-medium tracking-wider text-muted">CONFIDENCE</p>
          <p className="mt-1 font-mono text-2xl text-foreground">{(confidence * 100).toFixed(0)}%</p>
        </div>
      </div>
      <p className="mt-3 text-xs text-muted">
        Cohort statistics, not a trained model. Confidence reflects sample size, not
        certainty. See docs/architecture.md for the exact calibration.
      </p>
    </div>
  );
}
