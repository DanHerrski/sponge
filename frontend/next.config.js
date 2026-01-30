/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export for GitHub Pages
  output: 'export',

  // Disable image optimization (not supported in static export)
  images: {
    unoptimized: true,
  },

  // Base path for GitHub Pages (update if using custom domain)
  // basePath: '/sponge', // Uncomment if deploying to github.io/sponge

  // Trailing slashes for static hosting compatibility
  trailingSlash: true,

  // Environment variables exposed to client
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:54321/functions/v1/api',
  },
};

module.exports = nextConfig;
