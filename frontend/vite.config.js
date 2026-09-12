import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The dev server proxies API traffic to Flask so the browser only ever talks to
// one origin — no CORS involved during local development. In Docker, nginx does
// the same job (see frontend/nginx.conf).
const API_TARGET = process.env.VITE_API_TARGET ?? 'http://127.0.0.1:5000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true },
      '/health': { target: API_TARGET, changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setupTests.js'],
    css: false,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/main.jsx', 'src/setupTests.js'],
    },
  },
})
