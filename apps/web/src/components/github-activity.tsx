"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { formatRelativeTime } from "@/lib/format";

interface Commit {
  repo: string;
  sha: string;
  message: string;
  author: string;
  url: string;
  date: string;
}

interface PullRequest {
  repo: string;
  number: number;
  title: string;
  state: string;
  author: string;
  url: string;
  updated_at: string;
}

interface Activity {
  commits: Commit[];
  pull_requests: PullRequest[];
}

type Status = "loading" | "no-github" | "error" | "empty" | "ready";

export function GitHubActivity() {
  const [status, setStatus] = useState<Status>("loading");
  const [activity, setActivity] = useState<Activity | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch("/v1/github/activity")
      .then(async (r) => {
        if (cancelled) return;
        if (r.status === 403) {
          setStatus("no-github");
          return;
        }
        if (!r.ok) {
          setStatus("error");
          return;
        }
        const data: Activity = await r.json();
        setActivity(data);
        setStatus(data.commits.length === 0 && data.pull_requests.length === 0 ? "empty" : "ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "no-github") return null;

  return (
    <div className="feature-item mb-10" style={{ "--fade-delay": "0.45s" } as React.CSSProperties}>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium tracking-wider text-muted">GITHUB ACTIVITY · LIVE</p>
        {status === "ready" && (
          <span className="flex items-center gap-1.5 text-[10px] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-success glow-pulse" />
            synced just now
          </span>
        )}
      </div>

      {status === "loading" && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="skeleton h-24 rounded-lg" />
          <div className="skeleton h-24 rounded-lg" />
        </div>
      )}

      {status === "error" && (
        <div className="rounded-lg border border-dashed border-border p-5 text-sm text-muted">
          Couldn&apos;t reach GitHub just now - this refreshes automatically next visit.
        </div>
      )}

      {status === "empty" && (
        <div className="rounded-lg border border-dashed border-border p-5 text-sm text-muted">
          No recent commits or pull requests found on your repos yet.
        </div>
      )}

      {status === "ready" && activity && (
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <div className="rounded-lg border border-border bg-surface p-4">
            <p className="mb-3 text-xs font-medium text-foreground">Recent commits</p>
            <div className="space-y-3">
              {activity.commits.slice(0, 5).map((c) => (
                <a
                  key={`${c.repo}-${c.sha}`}
                  href={c.url}
                  target="_blank"
                  rel="noreferrer"
                  className="group block transition-opacity duration-150 hover:opacity-70"
                >
                  <p className="truncate text-xs text-foreground">{c.message}</p>
                  <p className="mt-0.5 flex items-center gap-1.5 text-[10px] text-muted">
                    <span className="font-mono">{c.sha}</span>
                    <span>·</span>
                    <span className="truncate">{c.repo.split("/")[1]}</span>
                    <span>·</span>
                    <span>{formatRelativeTime(c.date)}</span>
                  </p>
                </a>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface p-4">
            <p className="mb-3 text-xs font-medium text-foreground">Pull requests</p>
            <div className="space-y-3">
              {activity.pull_requests.length === 0 && (
                <p className="text-xs text-muted">No open or recent pull requests.</p>
              )}
              {activity.pull_requests.slice(0, 5).map((p) => (
                <a
                  key={`${p.repo}-${p.number}`}
                  href={p.url}
                  target="_blank"
                  rel="noreferrer"
                  className="group block transition-opacity duration-150 hover:opacity-70"
                >
                  <div className="flex items-center gap-2">
                    <PrStateBadge state={p.state} />
                    <p className="truncate text-xs text-foreground">{p.title}</p>
                  </div>
                  <p className="mt-0.5 text-[10px] text-muted">
                    {p.repo.split("/")[1]} #{p.number} · {formatRelativeTime(p.updated_at)}
                  </p>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PrStateBadge({ state }: { state: string }) {
  const styles: Record<string, string> = {
    merged: "bg-accent/15 text-accent",
    open: "bg-success/15 text-success",
    closed: "bg-danger/15 text-danger",
  };
  return (
    <span className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${styles[state] ?? "bg-surface-2 text-muted"}`}>
      {state}
    </span>
  );
}
