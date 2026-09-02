"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { GitHubRepo } from "@/lib/types";

export function LinkRepo({ projectId, currentRepo }: { projectId: string; currentRepo: string | null }) {
  const router = useRouter();
  const [repos, setRepos] = useState<GitHubRepo[] | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "no-github" | "error">("idle");
  const [selected, setSelected] = useState("");
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open || repos !== null) return;
    setStatus("loading");
    apiFetch("/v1/github/repos")
      .then(async (r) => {
        if (r.status === 403) {
          setStatus("no-github");
          return;
        }
        if (!r.ok) {
          setStatus("error");
          return;
        }
        const data = await r.json();
        setRepos(data.items);
        setStatus("idle");
      })
      .catch(() => setStatus("error"));
  }, [open, repos]);

  async function link(repoName: string) {
    setSaving(true);
    try {
      await apiFetch(`/v1/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify({ github_repo: repoName || null }),
      });
      router.refresh();
      setOpen(false);
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="rounded-md border border-border bg-surface-2 px-3 py-1.5 text-xs font-medium text-foreground transition-all duration-150 ease-premium hover:bg-border active:scale-[0.98]"
      >
        {currentRepo ? "Change linked repo" : "Link a GitHub repo"}
      </button>
    );
  }

  return (
    <div className="animate-fade-in rounded-lg border border-border bg-surface p-4">
      {status === "loading" && <p className="text-xs text-muted">Loading your repos...</p>}
      {status === "no-github" && (
        <p className="text-xs text-muted">
          Sign in with GitHub (instead of the dashboard secret) to link a real repo.
        </p>
      )}
      {status === "error" && <p className="text-xs text-danger">Couldn&apos;t load your repos just now.</p>}
      {repos && (
        <div className="space-y-3">
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="w-full rounded-md border border-border bg-background px-3 py-2 font-mono text-sm text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
          >
            <option value="">Select a repo...</option>
            {repos.map((r) => (
              <option key={r.name} value={r.name}>
                {r.name} {r.private ? "(private)" : ""}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <button
              onClick={() => link(selected)}
              disabled={!selected || saving}
              className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 disabled:opacity-40"
            >
              {saving ? "Linking..." : "Link this repo"}
            </button>
            {currentRepo && (
              <button
                onClick={() => link("")}
                disabled={saving}
                className="rounded-md px-3 py-1.5 text-xs text-danger transition-colors duration-150 hover:bg-danger/10"
              >
                Unlink
              </button>
            )}
            <button
              onClick={() => setOpen(false)}
              className="ml-auto rounded-md px-3 py-1.5 text-xs text-muted transition-colors duration-150 hover:text-foreground"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
