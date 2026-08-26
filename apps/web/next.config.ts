import type { NextConfig } from "next";

const apiInternalUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Proxying keeps the browser talking to a single origin so the backend's
    // httponly session cookie is set on that same origin instead of being
    // dropped as cross-origin (localhost:3000 vs localhost:8000 / api:8000).
    return [
      {
        source: "/api/:path*",
        destination: `${apiInternalUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
