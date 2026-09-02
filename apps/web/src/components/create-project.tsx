"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { GitHubRepo } from "@/lib/types";

interface Created {
  id: string;
  name: string;
  api_key: string;
  agent_id: string;
  agent_config_id: string;
}

type Tab = "github" | "manual";
type RepoStatus = "idle" | "loading" | "no-github" | "error" | "ready";

export function CreateProject() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("github");
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<Created | null>(null);
  const [copied, setCopied] = useState(false);

  const [repos, setRepos] = useState<GitHubRepo[] | null>(null);
  const [repoStatus, setRepoStatus] = useState<RepoStatus>("idle");
  const [selectedRepo, setSelectedRepo] = useState<string>("");

  useEffect(() => {
    if (!open || repos !== null) return;
    setRepoStatus("loading");
    apiFetch("/v1/github/repos")
      .then(async (r) => {
        if (r.status === 403) {
          setRepoStatus("no-github");
          setTab("manual");
          return;
        }
        if (!r.ok) {
          setRepoStatus("error");
          return;
        }
        const data = await r.json();
        setRepos(data.items);
        setRepoStatus("ready");
      })
      .catch(() => setRepoStatus("error"));
  }, [open, repos]);

  async function createFromRepo(repo: GitHubRepo) {
    setSaving(true);
    setError(null);
    try {
      const res = await apiFetch("/v1/projects", {
        method: "POST",
        body: JSON.stringify({ name: repo.name.split("/")[1] ?? repo.name, github_repo: repo.name }),
      });
      if (!res.ok) {
        setError("Could not create the project.");
        return;
      }
      setCreated(await res.json());
    } catch {
      setError("Could not reach the Kosma API.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateManual(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await apiFetch("/v1/projects", {
        method: "POST",
        body: JSON.stringify({ name: name.trim() }),
      });
      if (!res.ok) {
        setError("Could not create the project.");
        return;
      }
      setCreated(await res.json());
    } catch {
      setError("Could not reach the Kosma API.");
    } finally {
      setSaving(false);
    }
  }

  function close() {
    setOpen(false);
    setName("");
    setCreated(null);
    setError(null);
    setCopied(false);
    setSelectedRepo("");
    if (created) router.refresh();
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 active:scale-[0.98]"
      >
        + New project
      </button>
    );
  }

  const snippet = created
    ? `curl -X POST https://kosma-wb46.onrender.com/v1/traces \\
  -H "Authorization: Bearer ${created.api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "trace_ref": "unique-id-per-call",
    "agent_id": "${created.agent_id}",
    "agent_config_id": "${created.agent_config_id}",
    "input_text": "what your agent received",
    "success": true,
    "latency_ms": 420,
    "input_tokens": 120,
    "output_tokens": 80
  }'`
    : "";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={(e) => e.target === e.currentTarget && close()}
    >
      <div className="animate-fade-in w-full max-w-lg rounded-xl border border-border bg-surface p-6 shadow-lg">
        {!created ? (
          <>
            <h3 className="font-mono text-lg text-foreground">New project</h3>
            <p className="mt-1 text-sm text-muted">
              Creates a real project with a live API key you can start sending traces
              to right away.
            </p>

            <div className="mt-4 flex overflow-hidden rounded-md border border-border">
              <button
                onClick={() => setTab("github")}
                className={`flex-1 px-3 py-1.5 text-xs font-medium transition-colors duration-150 ${
                  tab === "github" ? "bg-accent text-accent-foreground" : "bg-surface-2 text-muted hover:text-foreground"
                }`}
              >
                Import from GitHub
              </button>
              <button
                onClick={() => setTab("manual")}
                className={`flex-1 px-3 py-1.5 text-xs font-medium transition-colors duration-150 ${
                  tab === "manual" ? "bg-accent text-accent-foreground" : "bg-surface-2 text-muted hover:text-foreground"
                }`}
              >
                Manual
              </button>
            </div>

            {tab === "github" ? (
              <div className="mt-4">
                {repoStatus === "loading" && <p className="text-xs text-muted">Loading your repos...</p>}
                {repoStatus === "no-github" && (
                  <p className="text-xs text-muted">
                    Sign in with GitHub (instead of the dashboard secret) to import a real
                    repo directly, or use Manual.
                  </p>
                )}
                {repoStatus === "error" && (
                  <p className="text-xs text-danger">Couldn&apos;t load your repos just now.</p>
                )}
                {repos && repos.length === 0 && (
                  <p className="text-xs text-muted">No repos found on your GitHub account.</p>
                )}
                {repos && repos.length > 0 && (
                  <div className="max-h-64 space-y-1 overflow-y-auto">
                    {repos.map((repo) => (
                      <button
                        key={repo.name}
                        onClick={() => {
                          setSelectedRepo(repo.name);
                          createFromRepo(repo);
                        }}
                        disabled={saving}
                        className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-left transition-colors duration-150 ${
                          selectedRepo === repo.name
                            ? "border-accent/40 bg-accent/5"
                            : "border-border bg-background hover:bg-surface-2"
                        } disabled:opacity-50`}
                      >
                        <div className="min-w-0">
                          <p className="truncate font-mono text-xs text-foreground">{repo.name}</p>
                          {repo.description && (
                            <p className="truncate text-[11px] text-muted">{repo.description}</p>
                          )}
                        </div>
                        {repo.private && (
                          <span className="ml-2 shrink-0 rounded bg-surface-2 px-1.5 py-0.5 text-[9px] text-muted">
                            private
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
                {error && <p className="mt-2 text-xs text-danger">{error}</p>}
              </div>
            ) : (
              <form onSubmit={handleCreateManual} className="mt-4 space-y-4">
                <div>
                  <label htmlFor="project-name" className="mb-1.5 block text-xs font-medium text-muted">
                    PROJECT NAME
                  </label>
                  <input
                    id="project-name"
                    autoFocus
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="My Support Agent"
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
                  />
                </div>
                {error && <p className="text-sm text-danger">{error}</p>}
                <div className="flex items-center gap-2">
                  <button
                    type="submit"
                    disabled={saving || name.trim().length === 0}
                    className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 disabled:opacity-40"
                  >
                    {saving ? "Creating..." : "Create project"}
                  </button>
                  <button
                    type="button"
                    onClick={close}
                    className="rounded-md px-3 py-2 text-sm text-muted transition-colors duration-150 hover:text-foreground"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}

            {tab === "github" && (
              <button
                onClick={close}
                className="mt-4 text-xs text-muted transition-colors duration-150 hover:text-foreground"
              >
                Cancel
              </button>
            )}
          </>
        ) : (
          <>
            <h3 className="font-mono text-lg text-foreground">{created.name} is ready</h3>
            <p className="mt-1 text-sm text-warning">
              Your API key is shown once - copy it now, it can&apos;t be retrieved again.
            </p>
            <div className="mt-4 flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2">
              <code className="flex-1 overflow-x-auto whitespace-nowrap font-mono text-xs text-foreground">
                {created.api_key}
              </code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(created.api_key);
                  setCopied(true);
                }}
                className="shrink-0 rounded-md border border-border px-2 py-1 text-xs text-foreground transition-colors duration-150 hover:bg-surface-2"
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="mb-1.5 mt-5 text-xs font-medium text-muted">SEND YOUR FIRST REAL TRACE</p>
            <pre className="overflow-x-auto rounded-md border border-border bg-background p-3 font-mono text-[11px] leading-relaxed text-foreground/90">
              {snippet}
            </pre>
            <button
              onClick={close}
              className="mt-5 w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm font-medium text-foreground transition-all duration-150 ease-premium hover:bg-border"
            >
              Done
            </button>
          </>
        )}
      </div>
    </div>
  );
}
