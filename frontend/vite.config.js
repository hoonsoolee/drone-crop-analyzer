import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/upload': 'http://localhost:8000',
      '/stitch': 'http://localhost:8000',
      '/analysis': 'http://localhost:8000',
      '/outputs': 'http://localhost:8000',
    },
  },
})
