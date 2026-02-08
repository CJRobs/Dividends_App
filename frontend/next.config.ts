import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Production optimizations
  compiler: {
    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // Experimental optimizations
  experimental: {
    // Optimize package imports for faster builds
    optimizePackageImports: [
      'lucide-react',
      'recharts',
      '@radix-ui/react-dialog',
      '@radix-ui/react-dropdown-menu',
      '@radix-ui/react-select',
    ],
  },

  // Bundle analyzer (run with ANALYZE=true npm run build)
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Client-side bundle optimizations
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          // Separate Plotly into its own chunk (it's heavy ~3MB)
          plotly: {
            test: /[\\/]node_modules[\\/](plotly\.js|react-plotly\.js)[\\/]/,
            name: 'plotly',
            priority: 10,
            reuseExistingChunk: true,
          },
          // Separate chart libraries
          charts: {
            test: /[\\/]node_modules[\\/](recharts|d3-.*)[\\/]/,
            name: 'charts',
            priority: 9,
            reuseExistingChunk: true,
          },
          // UI library chunks
          ui: {
            test: /[\\/]node_modules[\\/](@radix-ui)[\\/]/,
            name: 'ui',
            priority: 8,
            reuseExistingChunk: true,
          },
          // Common vendor chunk
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendor',
            priority: 5,
            reuseExistingChunk: true,
          },
        },
      };
    }

    return config;
  },
};

export default nextConfig;
