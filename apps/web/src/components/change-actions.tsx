"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export function GenerateRegressionSuiteButton({ impactReportId }: { impactReportId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState<number | null>(null);

  async function handleClick() {
    setLoading(true);
    try {
      const res = await apiFetch(`/v1/impact-reports/${impactReportId}/regression-tests`, {
        method: "POST",
      });
      if (res.ok) {
        const body = await res.json();
        setCount(body.total);
        router.refresh();
      }
    } finally {
      setLoading(false);
    }
  }

  if (count !== null) {
    return <p className="text-sm text-success">Generated {count} regression tests.</p>;
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="rounded-md border border-border bg-surface-2 px-3 py-1.5 text-xs font-medium text-foreground transition-all duration-150 ease-premium hover:bg-border active:scale-[0.98] disabled:opacity-40"
    >
      {loading ? "Generating..." : "Generate Regression Suite"}
    </button>
  );
}

export function ShipButton({ proposalId }: { proposalId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/v1/change-proposals/${proposalId}/ship`, { method: "POST" });
      if (!res.ok) throw new Error("Could not ship this change.");
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
        className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 active:scale-[0.98] disabled:opacity-40"
      >
        {loading ? "Shipping..." : "Ship this change"}
      </button>
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  );
}
