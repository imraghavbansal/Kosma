"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { Agent } from "@/lib/types";

export function ProposeChangeForm({ agents }: { agents: Agent[] }) {
  const router = useRouter();
  const [agentId, setAgentId] = useState(agents[0]?.id ?? "");
  const agent = agents.find((a) => a.id === agentId);
  const baseline = agent?.configs.find((c) => c.is_baseline);
  const candidates = agent?.configs.filter((c) => !c.is_baseline) ?? [];
  const [candidateId, setCandidateId] = useState(candidates[0]?.id ?? "");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState<"idle" | "creating" | "analyzing">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!baseline || !candidateId) return;
    setError(null);
    setLoading("creating");
    try {
      const createRes = await apiFetch("/v1/change-proposals", {
        method: "POST",
        body: JSON.stringify({
          agent_id: agentId,
          baseline_config_id: baseline.id,
          candidate_config_id: candidateId,
          description: description || null,
        }),
      });
      if (!createRes.ok) throw new Error("Could not create change proposal.");
      const proposal = await createRes.json();

      setLoading("analyzing");
      const analyzeRes = await apiFetch(`/v1/change-proposals/${proposal.id}/analyze`, {
        method: "POST",
      });
      if (!analyzeRes.ok) throw new Error("Analysis failed.");

      router.push(`/dashboard/changes/${proposal.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading("idle");
    }
  }

  if (!agent || !baseline) {
    return (
      <p className="text-sm text-muted">
        No agent with a baseline config found. Run the demo agent&apos;s seed script first.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-border bg-surface p-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted">BASELINE (current)</label>
          <div className="rounded-md border border-border bg-surface-2 px-3 py-2 font-mono text-sm text-foreground">
            {baseline.version_label}
          </div>
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted">CANDIDATE (proposed)</label>
          <select
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
            className="w-full rounded-md border border-border bg-background px-3 py-2 font-mono text-sm text-foreground outline-none transition-colors duration-150 focus:border-accent"
          >
            {candidates.map((c) => (
              <option key={c.id} value={c.id}>
                {c.version_label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1.5 block text-xs font-medium text-muted">DESCRIPTION (optional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          placeholder="What changed and why you're proposing it"
          className="w-full resize-none rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none transition-colors duration-150 focus:border-accent"
        />
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <button
        type="submit"
        disabled={loading !== "idle" || candidates.length === 0}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 active:scale-[0.98] disabled:opacity-40"
      >
        {loading === "creating" && "Creating proposal..."}
        {loading === "analyzing" && "Analyzing against historical cohort..."}
        {loading === "idle" && "Analyze this change"}
      </button>
    </form>
  );
}
