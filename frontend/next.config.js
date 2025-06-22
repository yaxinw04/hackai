/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  // Enable standalone output for Docker
  output: 'standalone',
  // Configure image optimization for production
  images: {
    unoptimized: true
  },
  // Environment variables validation
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig 