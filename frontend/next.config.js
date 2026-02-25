/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Only expose the centralized backend API URL
    NEXT_PUBLIC_BACKEND_API_URL: process.env.NEXT_PUBLIC_BACKEND_API_URL,
    NEXT_PUBLIC_BETTER_AUTH_URL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL,
  },
};

module.exports = nextConfig;