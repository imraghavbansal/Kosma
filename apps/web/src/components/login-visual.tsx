const DECORATIVE_BARS = [
  { label: "account_change / domestic", pct: 78, positive: true, delay: 0 },
  { label: "order_status / international", pct: 62, positive: true, delay: 0.1 },
  { label: "refund / domestic", pct: 45, positive: true, delay: 0.2 },
  { label: "refund / international", pct: 90, positive: false, delay: 0.3 },
  { label: "order_status / domestic", pct: 30, positive: true, delay: 0.4 },
];

const FEATURES = [
  { title: "Blast Radius Diff", desc: "See which workflows and segments a change helps or breaks." },
  { title: "Ship / Modify / Block", desc: "One verdict, backed by evidence, not a gut call." },
  { title: "Prediction Scorecard", desc: "Kosma grades its own forecast against what actually happened." },
];

export function LoginVisual() {
  return (
    <div className="relative hidden h-full flex-col justify-center overflow-hidden border-l border-border bg-surface px-12 lg:flex">
      <div className="bg-grid bg-glow pointer-events-none absolute inset-0 opacity-[0.4]" />

      <div className="relative z-10 max-w-md">
        <p className="mb-1 text-[10px] font-medium tracking-wider text-muted">
          ILLUSTRATIVE - NOT LIVE DATA
        </p>
        <p className="mb-6 font-mono text-sm text-foreground/90">
          Blast Radius Diff for a candidate prompt change
        </p>

        <div className="space-y-3 rounded-lg border border-border bg-background/60 p-5 backdrop-blur-sm">
          {DECORATIVE_BARS.map((bar, i) => (
            <div key={bar.label} className="animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="mb-1 flex items-center justify-between text-[11px]">
                <span className="font-mono text-foreground/70">{bar.label}</span>
                <span className={bar.positive ? "text-success" : "text-danger"}>
                  {bar.positive ? "+" : "-"}
                  {bar.pct}%
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
                <div
                  className={`grow-bar h-full rounded-full ${bar.positive ? "bg-success/70" : "bg-danger/70"}`}
                  style={{ width: `${bar.pct}%`, animationDelay: `${bar.delay + 0.3}s` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-10 space-y-5">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className="feature-item flex items-start gap-3"
              style={{ "--fade-delay": `${0.6 + i * 0.15}s` } as React.CSSProperties}
            >
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              <div>
                <p className="text-sm font-medium text-foreground">{f.title}</p>
                <p className="text-xs text-muted">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
