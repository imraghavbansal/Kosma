import { NextRequest, NextResponse } from "next/server";

const SESSION_COOKIE_NAME = "kosma_session";
const PUBLIC_PATHS = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic = PUBLIC_PATHS.some((path) => pathname.startsWith(path));
  const hasSession = request.cookies.has(SESSION_COOKIE_NAME);

  if (!hasSession && !isPublic) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  if (hasSession && pathname === "/login") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // /api/* is excluded: it's a proxy to the backend (see next.config.ts), which
  // enforces its own auth. Gating it here too would block the login endpoint
  // itself - you'd need a session to reach the route that creates one.
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
