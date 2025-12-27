/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: process.env.NODE_ENV === "production" ? "standalone" : undefined,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  allowedDevOrigins: process.env.PUBLIC_URL ? [process.env.PUBLIC_URL] : [],
};

module.exports = nextConfig;
