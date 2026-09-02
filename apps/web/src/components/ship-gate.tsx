import type { Recommendation } from "@/lib/types";

const GATE_STYLE: Record<Recommendation, { bg: string; border: string; text: string; label: string }> = {
  SHIP: { bg: "bg-success/10", border: "border-success/30", text: "text-success", label: "SHIP" },
  MODIFY: { bg: "bg-warning/10", border: "border-warning/30", text: "text-warning", label: "MODIFY" },
  BLOCK: { bg: "bg-danger/10", border: "border-danger/30", text: "text-danger", label: "BLOCK" },
  INSUFFICIENT_EVIDENCE: {
    bg: "bg-surface-2",
    border: "border-border-strong",
    text: "text-muted",
    label: "INSUFFICIENT EVIDENCE",
  },
};

export function ShipGate({
  recommendation,
  confidence,
  evidenceBasis,
  limitations,
  recommendedNextAction,
  replayMethod,
}: {
  recommendation: Recommendation;
  confidence: number;
  evidenceBasis: string;
  limitations: string[];
  recommendedNextAction: string;
  replayMethod: "real_llm" | "mock";
}) {
  const style = GATE_STYLE[recommendation];
  return (
    <div className={`animate-fade-in rounded-lg border ${style.border} ${style.bg} p-5`}>
      <div className="mb-3 flex items-center justify-between">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${
            replayMethod === "real_llm"
              ? "bg-accent/10 text-accent ring-accent/20"
              : "bg-surface-2 text-muted ring-border-strong"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${replayMethod === "real_llm" ? "bg-accent" : "bg-muted"}`} />
          {replayMethod === "real_llm" ? "REAL LLM REPLAY" : "SIMULATED DEMO MODEL"}
        </span>
      </div>
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

      <p className="mt-4 text-xs text-foreground/80">{evidenceBasis}</p>

      {limitations.length > 0 && (
        <div className="mt-3">
          <p className="mb-1 text-[10px] font-medium tracking-wider text-muted">LIMITATIONS</p>
          <ul className="space-y-1">
            {limitations.map((l, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-muted">
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-muted" />
                {l}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 border-t border-border/60 pt-3">
        <p className="text-[10px] font-medium tracking-wider text-muted">RECOMMENDED NEXT ACTION</p>
        <p className={`mt-1 text-sm font-medium ${style.text}`}>{recommendedNextAction}</p>
      </div>
    </div>
  );
}
