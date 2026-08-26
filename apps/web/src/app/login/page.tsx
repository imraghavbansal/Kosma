"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [secret, setSecret] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiFetch("/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ secret }),
      });
      if (!res.ok) {
        setError("Invalid secret.");
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("Could not reach the TraceOS API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm rounded-lg border border-border bg-surface p-8">
        <div className="mb-8">
          <h1 className="font-mono text-lg tracking-tight text-foreground">TRACEOS</h1>
          <p className="mt-1 text-sm text-muted">
            Know what a change will break before you ship it.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="secret" className="mb-1.5 block text-xs font-medium text-muted">
              DASHBOARD SECRET
            </label>
            <input
              id="secret"
              type="password"
              autoFocus
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 font-mono text-sm text-foreground outline-none focus:border-accent"
              placeholder="••••••••••••"
            />
          </div>
          {error && <p className="text-sm text-danger">{error}</p>}
          <button
            type="submit"
            disabled={loading || secret.length === 0}
            className="w-full rounded-md bg-accent px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </main>
  );
}
