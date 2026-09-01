import { cookies } from "next/headers";

const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

/** Server Component fetch helper. Unlike the browser (see lib/api.ts's same-origin
 * proxy), a Server Component runs on the Next.js server and has no cookies of its
 * own - they're forwarded explicitly here. */
export async function serverApiFetch(path: string, init?: RequestInit): Promise<Response> {
  const cookieStore = await cookies();
  return fetch(`${API_INTERNAL_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      cookie: cookieStore.toString(),
    },
    cache: "no-store",
  });
}
