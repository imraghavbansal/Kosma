"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface MeResponse {
  authenticated: boolean;
  user: { github_username: string; display_name: string | null; avatar_url: string | null } | null;
}

export function UserBadge() {
  const [me, setMe] = useState<MeResponse | null>(null);

  useEffect(() => {
    apiFetch("/v1/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then(setMe)
      .catch(() => setMe(null));
  }, []);

  if (!me?.user) {
    return (
      <div className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-muted">
        <div className="h-6 w-6 rounded-full bg-surface-2" />
        <span>Shared session</span>
      </div>
    );
  }

  return (
    <div className="animate-fade-in flex items-center gap-2 rounded-md px-2 py-1.5">
      {me.user.avatar_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={me.user.avatar_url}
          alt={me.user.github_username}
          className="h-6 w-6 rounded-full ring-1 ring-border"
        />
      ) : (
        <div className="h-6 w-6 rounded-full bg-accent" />
      )}
      <span className="truncate text-xs text-foreground/80">
        {me.user.display_name ?? me.user.github_username}
      </span>
    </div>
  );
}
