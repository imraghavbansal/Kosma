"use client";

import type { SegmentMetrics } from "@/lib/types";

export function BlastRadiusDiff({
  segments,
  onSelectSegment,
  selectedSegment,
}: {
  segments: SegmentMetrics[];
  onSelectSegment?: (segment: string) => void;
  selectedSegment?: string | null;
}) {
  const sorted = [...segments].sort((a, b) => a.success_delta - b.success_delta);
  const maxAbsDelta = Math.max(...sorted.map((s) => Math.abs(s.success_delta)), 0.05);
  const clickable = Boolean(onSelectSegment);

  return (
    <div className="space-y-2.5">
      {sorted.map((segment, i) => {
        const pct = (segment.success_delta / maxAbsDelta) * 50; // % of half-width
        const isRegression = segment.success_delta < 0;
        const isSelected = selectedSegment === segment.segment;
        return (
          <div
            key={segment.segment}
            onClick={clickable ? () => onSelectSegment?.(segment.segment) : undefined}
            role={clickable ? "button" : undefined}
            tabIndex={clickable ? 0 : undefined}
            onKeyDown={
              clickable
                ? (e) => {
                    if (e.key === "Enter" || e.key === " ") onSelectSegment?.(segment.segment);
                  }
                : undefined
            }
            className={`stagger-fade-in group rounded-md transition-colors duration-150 ${
              clickable ? "cursor-pointer" : ""
            } ${isSelected ? "bg-surface-2 ring-1 ring-accent/40" : "hover:bg-surface-2/40"}`}
            style={{ "--fade-delay": `${i * 0.08}s` } as React.CSSProperties}
          >
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
            <div className="relative h-5 overflow-hidden rounded bg-surface-2 ring-1 ring-inset ring-border">
              <div className="absolute left-1/2 top-0 z-10 h-full w-px bg-border-strong" />
              <div
                className={`grow-bar absolute top-0 h-full rounded-sm shadow-[0_0_10px_-2px] ${
                  isRegression
                    ? "origin-right bg-danger shadow-danger/50"
                    : "origin-left bg-success shadow-success/50"
                }`}
                style={
                  isRegression
                    ? { right: "50%", width: `${Math.abs(pct)}%`, animationDelay: `${0.2 + i * 0.08}s` }
                    : { left: "50%", width: `${Math.abs(pct)}%`, animationDelay: `${0.2 + i * 0.08}s` }
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
