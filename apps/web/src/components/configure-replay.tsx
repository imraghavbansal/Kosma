"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export function ConfigureReplay({
  projectId,
  configured,
  provider,
}: {
  projectId: string;
  configured: boolean;
  provider: string | null;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState(provider ?? "openai");
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (!apiKey.trim()) {
      setError("API key is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const res = await apiFetch(`/v1/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify({ llm_provider: selectedProvider, llm_api_key: apiKey.trim() }),
      });
      if (!res.ok) {
        setError("Could not save.");
        return;
      }
      setApiKey("");
      setOpen(false);
      router.refresh();
    } finally {
      setSaving(false);
    }
  }

  async function disable() {
    if (!confirm("Turn off real replay? Future analyses on this project will use the simulated demo model.")) return;
    setSaving(true);
    try {
      await apiFetch(`/v1/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify({ llm_provider: null, llm_api_key: null }),
      });
      router.refresh();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-foreground">Real counterfactual replay</p>
          <p className="mt-1 text-xs text-muted">
            {configured ? (
              <>
                Configured - analysis on this project calls a real{" "}
                <span className="font-mono">{provider}</span> model, judged by a second real
                model call.
              </>
            ) : (
              "Not configured - analysis uses the simulated demo model, clearly labeled as such on every report."
            )}
          </p>
        </div>
        {configured ? (
          <button
            onClick={disable}
            disabled={saving}
            className="shrink-0 rounded-md border border-border px-3 py-1.5 text-xs text-danger transition-colors duration-150 hover:bg-danger/10"
          >
            Turn off
          </button>
        ) : (
          !open && (
            <button
              onClick={() => setOpen(true)}
              className="shrink-0 rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90"
            >
              Configure
            </button>
          )
        )}
      </div>

      {open && !configured && (
        <div className="animate-fade-in mt-4 space-y-3 border-t border-border pt-4">
          <div className="flex overflow-hidden rounded-md border border-border">
            {(["openai", "anthropic"] as const).map((p) => (
              <button
                key={p}
                onClick={() => setSelectedProvider(p)}
                className={`flex-1 px-3 py-1.5 text-xs font-medium capitalize transition-colors duration-150 ${
                  selectedProvider === p
                    ? "bg-accent text-accent-foreground"
                    : "bg-surface-2 text-muted hover:text-foreground"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={selectedProvider === "openai" ? "sk-..." : "sk-ant-..."}
            className="w-full rounded-md border border-border bg-background px-3 py-2 font-mono text-xs text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
          />
          {error && <p className="text-xs text-danger">{error}</p>}
          <p className="text-[10px] text-muted">
            Stored on this project only, never returned by the API again. Real replay
            calls this provider once per replayed trace plus once to judge the
            result - this has real cost.
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={save}
              disabled={saving}
              className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 disabled:opacity-40"
            >
              {saving ? "Saving..." : "Save"}
            </button>
            <button
              onClick={() => setOpen(false)}
              className="rounded-md px-3 py-1.5 text-xs text-muted transition-colors duration-150 hover:text-foreground"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
