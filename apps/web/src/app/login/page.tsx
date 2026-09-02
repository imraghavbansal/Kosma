"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { ThemeToggle } from "@/components/theme-toggle";
import { LoginVisual } from "@/components/login-visual";

export default function LoginPage() {
  const router = useRouter();
  const [secret, setSecret] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showOwnerAccess, setShowOwnerAccess] = useState(false);

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
    <main className="grid min-h-screen bg-background lg:grid-cols-2">
      <div className="relative flex items-center justify-center px-4">
        <div className="bg-grid pointer-events-none absolute inset-0 opacity-[0.15] lg:hidden" />
        <div className="absolute right-6 top-6">
          <ThemeToggle />
        </div>

        <div className="relative z-10 w-full max-w-sm animate-fade-in">
          <div className="mb-8">
            <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-md bg-accent font-mono text-sm font-bold text-accent-foreground">
              K
            </div>
            <h1 className="font-mono text-lg tracking-tight text-foreground">KOSMA</h1>
            <p className="mt-1 text-sm text-muted">
              Know what a change will break before you ship it.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-surface p-8 shadow-sm">
            <a
              href="/api/v1/auth/github/login"
              className="flex w-full items-center justify-center gap-2 rounded-md bg-accent px-3 py-2.5 text-sm font-medium text-accent-foreground transition-all duration-150 ease-premium hover:opacity-90 active:scale-[0.98]"
            >
              <svg viewBox="0 0 16 16" className="h-4 w-4 fill-current" aria-hidden="true">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
              </svg>
              Continue with GitHub
            </a>
            <p className="mt-3 text-center text-xs text-muted">
              No signup needed. Your account is created on first sign-in.
            </p>

            {!showOwnerAccess ? (
              <button
                onClick={() => setShowOwnerAccess(true)}
                className="mt-6 w-full text-center text-xs text-muted transition-colors duration-150 hover:text-foreground"
              >
                Project owner? Sign in with the dashboard secret instead
              </button>
            ) : (
              <div className="animate-fade-in mt-6">
                <div className="mb-4 flex items-center gap-3">
                  <div className="h-px flex-1 bg-border" />
                  <span className="text-[10px] font-medium tracking-wider text-muted">OWNER ACCESS</span>
                  <div className="h-px flex-1 bg-border" />
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
                    className="w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm font-medium text-foreground transition-all duration-150 ease-premium hover:bg-border active:scale-[0.98] disabled:opacity-40 disabled:active:scale-100"
                  >
                    {loading ? "Signing in..." : "Sign in"}
                  </button>
                </form>
              </div>
            )}
          </div>

          <p className="mt-6 text-center text-xs text-muted">
            GitHub and the owner secret both grant an equally-privileged session on
            this single-tenant deployment - see <span className="font-mono">docs/architecture.md</span>.
          </p>
        </div>
      </div>

      <LoginVisual />
    </main>
  );
}
