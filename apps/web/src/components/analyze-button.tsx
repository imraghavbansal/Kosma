"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export function AnalyzeButton({ proposalId }: { proposalId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/v1/change-proposals/${proposalId}/analyze`, { method: "POST" });
      if (!res.ok) throw new Error("Analysis failed.");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={loading}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 active:scale-[0.98] disabled:opacity-40"
      >
        {loading ? "Analyzing against historical cohort..." : "Analyze this change"}
      </button>
      {error && <p className="mt-2 text-sm text-danger">{error}</p>}
    </div>
  );
}
