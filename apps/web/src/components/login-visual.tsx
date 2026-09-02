"use client";

import { useEffect, useState } from "react";
import { BlastRadiusDiff } from "@/components/blast-radius-diff";
import { CountUp } from "@/components/count-up";
import type { SegmentMetrics } from "@/lib/types";

const FEATURES = [
  { title: "Blast Radius Diff", desc: "See which workflows and segments a change helps or breaks." },
  { title: "Ship / Modify / Block", desc: "One verdict, backed by evidence, not a gut call." },
  { title: "Prediction Scorecard", desc: "Kosma grades its own forecast against what actually happened." },
];

interface PublicStats {
  total_traces: number;
  total_analyzed_changes: number;
  latest_impact_report: {
    recommendation: string;
    confidence: number;
    segment_metrics: SegmentMetrics[];
  } | null;
}

export function LoginVisual() {
  const [stats, setStats] = useState<PublicStats | null>(null);

  useEffect(() => {
    fetch("/api/v1/public/stats")
      .then((r) => (r.ok ? r.json() : null))
      .then(setStats)
      .catch(() => setStats(null));
  }, []);

  const report = stats?.latest_impact_report;

  return (
    <div className="relative hidden h-full flex-col justify-center overflow-hidden border-l border-border bg-surface px-12 lg:flex">
      <div className="bg-grid bg-glow pointer-events-none absolute inset-0 opacity-[0.4]" />

      <div className="relative z-10 max-w-md">
        {stats && (
          <div className="animate-fade-in mb-6 flex items-center gap-6 font-mono text-xs text-muted">
            <span>
              <span className="text-lg text-foreground">
                <CountUp value={stats.total_traces} />
              </span>{" "}
              traces analyzed
            </span>
            <span>
              <span className="text-lg text-foreground">
                <CountUp value={stats.total_analyzed_changes} />
              </span>{" "}
              changes evaluated
            </span>
          </div>
        )}

        <p className="mb-1 text-[10px] font-medium tracking-wider text-muted">
          {report ? "REAL BLAST RADIUS DIFF - LIVE DEMO DATA" : "BLAST RADIUS DIFF"}
        </p>
        <p className="mb-6 font-mono text-sm text-foreground/90">
          {report
            ? "The most recent change proposal, analyzed against real replayed traffic"
            : "Propose a change to see this fill in with real data"}
        </p>

        {report ? (
          <div className="animate-fade-in rounded-lg border border-border bg-background/60 p-5 backdrop-blur-sm">
            <BlastRadiusDiff segments={report.segment_metrics} />
          </div>
        ) : (
          <div className="space-y-3 rounded-lg border border-dashed border-border p-5">
            <div className="skeleton h-3 w-full rounded" />
            <div className="skeleton h-3 w-4/5 rounded" />
            <div className="skeleton h-3 w-3/5 rounded" />
          </div>
        )}

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
