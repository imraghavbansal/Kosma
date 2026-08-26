"use client";

import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    await apiFetch("/v1/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <button
      onClick={handleLogout}
      className="mt-4 rounded-md px-2 py-1.5 text-left text-sm text-muted transition-colors hover:bg-surface hover:text-foreground"
    >
      Sign out
    </button>
  );
}
