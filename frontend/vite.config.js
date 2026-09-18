import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  base: '/static/',
  plugins: [svelte()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  }
})
