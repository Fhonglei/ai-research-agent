/** @type {import('next').NextConfig} */
const isProduction = process.env.NODE_ENV === 'production'

const nextConfig = {
  // Static export for GitHub Pages (production only)
  ...(isProduction ? {
    output: 'export',
    basePath: '/ai-research-agent',
    assetPrefix: '/ai-research-agent',
  } : {}),

  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
