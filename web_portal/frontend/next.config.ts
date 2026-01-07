import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker production builds
  output: 'standalone',

  // Disable telemetry in production
  // eslint: {
  //   ignoreDuringBuilds: true,
  // },

  // Image optimization
  images: {
    unoptimized: process.env.NODE_ENV === 'production',
  },
};

export default nextConfig;
