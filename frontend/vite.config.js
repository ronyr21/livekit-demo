import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allow external access
    port: 5173,
    strictPort: true,    allowedHosts: [
      'localhost',
      'dee3-185-38-29-77.ngrok-free.app',
      '.ngrok-free.app',
      '.ngrok.io'
    ],
    hmr: {
      port: 5173,
      host: 'localhost'
    },
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "")
      }
    }
  }
})
