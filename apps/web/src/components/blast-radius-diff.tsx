"use client";

import type { SegmentMetrics } from "@/lib/types";

export function BlastRadiusDiff({ segments }: { segments: SegmentMetrics[] }) {
  const sorted = [...segments].sort((a, b) => a.success_delta - b.success_delta);
  const maxAbsDelta = Math.max(...sorted.map((s) => Math.abs(s.success_delta)), 0.05);

  return (
    <div className="space-y-2.5">
      {sorted.map((segment) => {
        const pct = (segment.success_delta / maxAbsDelta) * 50; // % of half-width
        const isRegression = segment.success_delta < 0;
        return (
          <div key={segment.segment} className="animate-fade-in">
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-mono text-foreground">
                {segment.workflow.replace("_", " ")} / {segment.region}
              </span>
              <span className={isRegression ? "text-danger" : "text-success"}>
                {segment.baseline_success_rate >= 0 && `${(segment.baseline_success_rate * 100).toFixed(0)}%`}
                {" -> "}
                {(segment.candidate_success_rate * 100).toFixed(0)}%
                {" ("}
                {isRegression ? "" : "+"}
                {(segment.success_delta * 100).toFixed(1)} pts{")"}
              </span>
            </div>
            <div className="relative h-5 overflow-hidden rounded bg-surface-2">
              <div className="absolute left-1/2 top-0 h-full w-px bg-border-strong" />
              <div
                className={`absolute top-0 h-full rounded transition-all duration-700 ease-premium ${
                  isRegression ? "bg-danger/70" : "bg-success/70"
                }`}
                style={
                  isRegression
                    ? { right: "50%", width: `${Math.abs(pct)}%` }
                    : { left: "50%", width: `${Math.abs(pct)}%` }
                }
              />
            </div>
            <p className="mt-0.5 text-[10px] text-muted">n={segment.sample_size} replayed</p>
          </div>
        );
      })}
    </div>
  );
}
