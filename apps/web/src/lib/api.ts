// All requests go through the Next.js rewrite at /api/* (see next.config.ts),
// which proxies to the FastAPI backend. This keeps the browser on one origin
// so the backend's httponly session cookie lands on that origin instead of
// being dropped as cross-origin.
export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`/api${path}`, {
    ...init,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
}
