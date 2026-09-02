"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";

interface MeResponse {
  authenticated: boolean;
  user: { github_username: string; display_name: string | null; avatar_url: string | null } | null;
}

export function UserMenu() {
  const router = useRouter();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiFetch("/v1/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then(setMe)
      .catch(() => setMe(null));
  }, []);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  async function handleLogout() {
    await apiFetch("/v1/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  const label = me?.user ? (me.user.display_name ?? me.user.github_username) : "Project owner";

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-full border border-transparent py-1 pl-1 pr-2.5 transition-all duration-150 ease-premium hover:border-border hover:bg-surface-2"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {me?.user?.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={me.user.avatar_url} alt={label} className="h-7 w-7 rounded-full ring-1 ring-border" />
        ) : (
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent font-mono text-xs font-bold text-accent-foreground">
            {label.slice(0, 1).toUpperCase()}
          </div>
        )}
        <span className="hidden max-w-[9rem] truncate text-sm text-foreground/85 sm:inline">{label}</span>
        <svg
          viewBox="0 0 12 12"
          className={`h-3 w-3 text-muted transition-transform duration-200 ease-premium ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <path d="M3 4.5l3 3 3-3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          className="animate-fade-in absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-lg border border-border bg-surface shadow-lg"
        >
          <div className="border-b border-border px-3 py-3">
            <p className="truncate text-sm font-medium text-foreground">{label}</p>
            <p className="truncate text-xs text-muted">
              {me?.user ? `@${me.user.github_username}` : "Shared-secret session"}
            </p>
          </div>
          <Link
            href="/dashboard/settings"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="block px-3 py-2 text-sm text-foreground/85 transition-colors duration-150 hover:bg-surface-2"
          >
            Settings
          </Link>
          <button
            onClick={handleLogout}
            role="menuitem"
            className="block w-full px-3 py-2 text-left text-sm text-danger transition-colors duration-150 hover:bg-danger/10"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
