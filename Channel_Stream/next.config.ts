import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // Static export — produces an /out directory of plain HTML/JS/CSS files.
  // These get uploaded to the portfolio's S3 bucket under /channel-stream/.
  output: "export",

  // Each page becomes a directory with index.html so S3 can serve it without
  // a web server. e.g. /sports → /sports/index.html
  trailingSlash: true,

  // In production the app lives at jonathanlohr.com/channel-stream.
  // NEXT_PUBLIC_BASE_PATH is injected by the CI build step; it is empty in dev
  // so localhost:3001 still works at root.
  basePath:    process.env.NEXT_PUBLIC_BASE_PATH ?? "",
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH ?? "",

  // Required for static export — Next.js Image Optimization needs a server.
  images: { unoptimized: true },
}

export default nextConfig
