import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The dev server proxies API traffic to Flask so the browser only ever talks to
// one origin — no CORS involved during local development.
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
})
