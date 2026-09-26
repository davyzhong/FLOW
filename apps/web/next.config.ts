import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  // Playwright and local tools often address this server through 127.0.0.1,
  // while Next dev binds/initializes against localhost by default.
  allowedDevOrigins: ["127.0.0.1"],
  output: "standalone",
};

export default nextConfig;
