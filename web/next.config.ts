import type { NextConfig } from "next";

// A static site: Vercel serves the files, and the ZenAI API runs beside it as a
// Python function under /api. Nothing here renders on a server.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
