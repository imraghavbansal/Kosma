"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

interface Created {
  id: string;
  name: string;
  api_key: string;
  agent_id: string;
  agent_config_id: string;
}

export function CreateProject() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<Created | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleCreate(e: React.FormEvent) {
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
            <form onSubmit={handleCreate} className="mt-5 space-y-4">
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
