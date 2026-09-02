"use client";

import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/badge";
import { BlastRadiusDiff } from "@/components/blast-radius-diff";
import type { ImpactEvidence, SegmentMetrics } from "@/lib/types";

export function BlastRadiusExplorer({
  segments,
  evidence,
}: {
  segments: SegmentMetrics[];
  evidence: ImpactEvidence[];
}) {
  const [selected, setSelected] = useState<string | null>(null);

  const filteredEvidence = selected ? evidence.filter((e) => e.segment === selected) : evidence.slice(0, 30);
  const selectedMetrics = segments.find((s) => s.segment === selected) ?? null;
  const [workflow, region] = selected ? selected.split(":") : [null, null];

  return (
    <div className="space-y-4">
      <div>
        <p className="mb-3 text-xs font-medium tracking-wider text-muted">
          BLAST RADIUS DIFF - BY WORKFLOW / SEGMENT
        </p>
        <div className="rounded-lg border border-border bg-surface p-5">
          <BlastRadiusDiff
            segments={segments}
            onSelectSegment={(segment) => setSelected((s) => (s === segment ? null : segment))}
            selectedSegment={selected}
          />
        </div>
      </div>

      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs font-medium tracking-wider text-muted">
            EVIDENCE - BASELINE VS REPLAY TRACE PAIRS
          </p>
          {selected && selectedMetrics ? (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted">Change</span>
              <span className="text-foreground">→</span>
              <span className="font-mono text-foreground">{workflow}</span>
              <span className="text-foreground">→</span>
              <Badge variant={selectedMetrics.success_delta < 0 ? "danger" : "success"}>{region}</Badge>
              <button
                onClick={() => setSelected(null)}
                className="ml-1 text-muted transition-colors duration-150 hover:text-foreground"
              >
                clear ×
              </button>
              <Link
                href={`/dashboard/failure-clusters`}
                className="ml-2 text-accent hover:underline"
              >
                view failure clusters for this workflow →
              </Link>
            </div>
          ) : (
            <span className="text-xs text-muted">Click a segment above to drill in</span>
          )}
        </div>

        {selectedMetrics && (
          <div className="mb-3 grid grid-cols-3 gap-3 sm:grid-cols-4">
            <MiniStat label="Sample size" value={String(selectedMetrics.sample_size)} />
            <MiniStat
              label="Baseline success"
              value={`${(selectedMetrics.baseline_success_rate * 100).toFixed(0)}%`}
            />
            <MiniStat
              label="Candidate success"
              value={`${(selectedMetrics.candidate_success_rate * 100).toFixed(0)}%`}
            />
            <MiniStat
              label="Delta"
              value={`${selectedMetrics.success_delta >= 0 ? "+" : ""}${(
                selectedMetrics.success_delta * 100
              ).toFixed(1)} pts`}
              danger={selectedMetrics.success_delta < 0}
            />
          </div>
        )}

        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-left text-xs text-muted">
                <th className="px-4 py-2 font-medium">Segment</th>
                <th className="px-4 py-2 font-medium">Tier</th>
                <th className="px-4 py-2 font-medium">Baseline trace</th>
                <th className="px-4 py-2 font-medium">Replay trace</th>
                <th className="px-4 py-2 font-medium">Note</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvidence.map((e) => (
                <tr key={e.id} className="border-b border-border last:border-0 hover:bg-surface-2">
                  <td className="px-4 py-2 text-xs text-foreground/80">{e.segment}</td>
                  <td className="px-4 py-2">
                    <Badge variant="neutral">{e.evidence_tier}</Badge>
                  </td>
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
        {!selected && evidence.length > 30 && (
          <p className="mt-2 text-xs text-muted">Showing 30 of {evidence.length} replayed pairs.</p>
        )}
        {selected && filteredEvidence.length === 0 && (
          <p className="mt-2 text-xs text-muted">No evidence rows for this segment.</p>
        )}
      </div>
    </div>
  );
}

function MiniStat({ label, value, danger }: { label: string; value: string; danger?: boolean }) {
  return (
    <div className="rounded-md border border-border bg-background p-2.5">
      <p className="text-[9px] font-medium tracking-wider text-muted">{label.toUpperCase()}</p>
      <p className={`mt-0.5 font-mono text-sm ${danger ? "text-danger" : "text-foreground"}`}>{value}</p>
    </div>
  );
}
