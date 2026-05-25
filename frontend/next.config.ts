import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Avoid Turbopack SST cache errors on Windows (path locks / os error 3).
  experimental: {
    turbopackFileSystemCacheForDev: false,
  },
};

export default nextConfig;
