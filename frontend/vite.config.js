import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  server: { proxy: { '/api': { target: 'http://localhost:81', changeOrigin: false } } },
  preview: { proxy: { '/api': { target: 'http://localhost:81', changeOrigin: false } } },
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src')
    }
  }
})
