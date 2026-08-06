import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Dev server: proxy API calls to the FastAPI backend
  // Run FastAPI on :8000 and this dev server on :5173
  server: {
    port: 5173,
    proxy: {
      '/chat': 'http://localhost:8000',
      '/plan': 'http://localhost:8000',
      '/sessions': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },

  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
