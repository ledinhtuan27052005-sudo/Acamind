/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Node.js 24 compatibility: override standalone output (not needed for dev)
  output: undefined,
  // Fix for Node.js 24 where generateBuildId may be undefined
  generateBuildId: async () => null,
  // Fix: transpile three.js + r3f so Next.js 14 App Router can bundle them correctly
  // Without this, @react-three/fiber throws "Cannot read properties of undefined"
  transpilePackages: ['three', '@react-three/fiber', '@react-three/drei'],
};

module.exports = nextConfig;
