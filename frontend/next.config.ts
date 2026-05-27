import type { NextConfig } from "next";

const backendApiUrl = (
  process.env.BACKEND_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const nextConfig: NextConfig = {
  allowedDevOrigins: ["*.trycloudflare.com"],
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendApiUrl}/api/v1/:path*`,
      },
      {
        source: "/ws/:path*",
        destination: `${backendApiUrl}/ws/:path*`,
      },
    ];
  },
};

export default nextConfig;
