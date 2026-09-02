"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export function NewConfigForm({ agentId }: { agentId: string }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [versionLabel, setVersionLabel] = useState("");
  const [kind, setKind] = useState<"prompt" | "model">("prompt");
  const [promptText, setPromptText] = useState("");
  const [modelProvider, setModelProvider] = useState("");
  const [modelName, setModelName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await apiFetch(`/v1/agents/${agentId}/configs`, {
        method: "POST",
        body: JSON.stringify({
          kind,
          version_label: versionLabel.trim(),
          prompt_text: promptText.trim() || null,
          model_provider: modelProvider.trim() || null,
          model_name: modelName.trim() || null,
        }),
      });
      if (!res.ok) {
        setError("Could not create the config.");
        return;
      }
      setVersionLabel("");
      setPromptText("");
      setModelProvider("");
      setModelName("");
      setOpen(false);
      router.refresh();
    } catch {
      setError("Could not reach the Kosma API.");
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full px-5 py-3 text-left text-xs font-medium text-accent transition-colors duration-150 hover:bg-surface-2"
      >
        + New config (e.g. a candidate to propose a change against)
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="animate-fade-in space-y-3 px-5 py-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-[10px] font-medium text-muted">VERSION LABEL</label>
          <input
            autoFocus
            value={versionLabel}
            onChange={(e) => setVersionLabel(e.target.value)}
            placeholder="v2-concise"
            className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
          />
        </div>
        <div>
          <label className="mb-1 block text-[10px] font-medium text-muted">KIND</label>
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as "prompt" | "model")}
            className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
          >
            <option value="prompt">prompt</option>
            <option value="model">model</option>
          </select>
        </div>
      </div>
      <div>
        <label className="mb-1 block text-[10px] font-medium text-muted">PROMPT TEXT (optional)</label>
        <textarea
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          rows={2}
          placeholder="The system prompt this version uses"
          className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-[10px] font-medium text-muted">MODEL PROVIDER</label>
          <input
            value={modelProvider}
            onChange={(e) => setModelProvider(e.target.value)}
            placeholder="openai"
            className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
          />
        </div>
        <div>
          <label className="mb-1 block text-[10px] font-medium text-muted">MODEL NAME</label>
          <input
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            placeholder="gpt-4o-mini"
            className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
          />
        </div>
      </div>
      {error && <p className="text-xs text-danger">{error}</p>}
      <div className="flex items-center gap-2">
        <button
          type="submit"
          disabled={saving || versionLabel.trim().length === 0}
          className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 disabled:opacity-40"
        >
          {saving ? "Creating..." : "Create config"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-md px-3 py-1.5 text-xs text-muted transition-colors duration-150 hover:text-foreground"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
