<<<<<<< HEAD
const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  webpack(config) {
    config.resolve.alias['@'] = path.resolve(__dirname, 'src');
    return config;
  },
=======
/** @type {import('next').NextConfig} */
const nextConfig = {
>>>>>>> bc57f41 (Initial CAR-BOOKING project)
  images: {
    domains: ['localhost'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
<<<<<<< HEAD
=======
  // PWA configuration
>>>>>>> bc57f41 (Initial CAR-BOOKING project)
  async headers() {
    return [
      {
        source: '/manifest.json',
        headers: [
          {
            key: 'Content-Type',
            value: 'application/manifest+json',
          },
        ],
      },
    ];
  },
<<<<<<< HEAD
=======
  // API proxy for development
>>>>>>> bc57f41 (Initial CAR-BOOKING project)
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

<<<<<<< HEAD
module.exports = nextConfig;
=======
module.exports = nextConfig;
>>>>>>> bc57f41 (Initial CAR-BOOKING project)
