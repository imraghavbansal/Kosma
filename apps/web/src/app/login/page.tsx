"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { ThemeToggle } from "@/components/theme-toggle";

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
      setError("Could not reach the Kosma API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-background px-4">
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-sm animate-fade-in rounded-xl border border-border bg-surface p-8 shadow-sm">
        <div className="mb-8">
          <h1 className="font-mono text-lg tracking-tight text-foreground">KOSMA</h1>
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
              className="w-full rounded-md border border-border bg-background px-3 py-2 font-mono text-sm text-foreground outline-none transition-colors duration-150 focus:border-accent focus:ring-2 focus:ring-accent/20"
              placeholder="••••••••••••"
            />
          </div>
          {error && <p className="animate-fade-in text-sm text-danger">{error}</p>}
          <button
            type="submit"
            disabled={loading || secret.length === 0}
            className="w-full rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 active:scale-[0.98] disabled:opacity-40 disabled:active:scale-100"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </main>
  );
}
