"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { formatRelativeTime } from "@/lib/format";
import type { GitHubRepoActivity } from "@/lib/types";

export function RepoActivityPanel({ repo }: { repo: string }) {
  const [activity, setActivity] = useState<GitHubRepoActivity | null>(null);
  const [status, setStatus] = useState<"loading" | "no-github" | "error" | "ready">("loading");

  useEffect(() => {
    let cancelled = false;
    apiFetch(`/v1/github/repos/${repo}/activity`)
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
        setActivity(await r.json());
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [repo]);

  if (status === "loading") {
    return (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="skeleton h-32 rounded-lg" />
        <div className="skeleton h-32 rounded-lg" />
      </div>
    );
  }

  if (status === "no-github") {
    return (
      <div className="rounded-lg border border-dashed border-border p-5 text-sm text-muted">
        Sign in with GitHub to see this repo&apos;s real activity here.
      </div>
    );
  }

  if (status === "error" || !activity) {
    return (
      <div className="rounded-lg border border-dashed border-border p-5 text-sm text-muted">
        Couldn&apos;t reach GitHub for {repo} just now.
      </div>
    );
  }

  return (
    <div className="animate-fade-in grid grid-cols-1 gap-3 sm:grid-cols-2">
      <div className="rounded-lg border border-border bg-surface p-4">
        <p className="mb-3 text-xs font-medium text-foreground">Commits</p>
        <div className="space-y-3">
          {activity.commits.length === 0 && <p className="text-xs text-muted">No commits found.</p>}
          {activity.commits.map((c) => (
            <a
              key={c.sha}
              href={c.url}
              target="_blank"
              rel="noreferrer"
              className="block transition-opacity duration-150 hover:opacity-70"
            >
              <p className="truncate text-xs text-foreground">{c.message}</p>
              <p className="mt-0.5 text-[10px] text-muted">
                <span className="font-mono">{c.sha}</span> · {c.author} · {formatRelativeTime(c.date)}
              </p>
            </a>
          ))}
        </div>
      </div>
      <div className="rounded-lg border border-border bg-surface p-4">
        <p className="mb-3 text-xs font-medium text-foreground">Pull requests</p>
        <div className="space-y-3">
          {activity.pull_requests.length === 0 && <p className="text-xs text-muted">No pull requests found.</p>}
          {activity.pull_requests.map((p) => (
            <a
              key={p.number}
              href={p.url}
              target="_blank"
              rel="noreferrer"
              className="block transition-opacity duration-150 hover:opacity-70"
            >
              <p className="truncate text-xs text-foreground">
                #{p.number} {p.title}
              </p>
              <p className="mt-0.5 text-[10px] text-muted">
                {p.state} · {p.author} · {formatRelativeTime(p.updated_at)}
              </p>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
