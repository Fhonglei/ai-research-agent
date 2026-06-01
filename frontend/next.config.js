/** @type {import('next').NextConfig} */
const isProduction = process.env.NODE_ENV === 'production'

const nextConfig = {
  // Static export for GitHub Pages
  output: 'export',

  // GitHub Pages serves from repo subdirectory
  basePath: isProduction ? '/ai-research-agent' : '',
  assetPrefix: isProduction ? '/ai-research-agent' : '',

  images: {
    unoptimized: true, // Required for static export
  },
}

module.exports = nextConfig
