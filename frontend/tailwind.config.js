/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{svelte,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'sans-serif'],
        display: ['Clash Display', 'sans-serif'],
        script: ['Caveat', 'cursive'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      colors: {
        foam: '#F5FAFA',
        surface: '#FFFFFF',
        surfaceDeep: '#EAF3F4',
        ink: '#0E2A33',
        inkSoft: '#56727C',
        deep: '#073B4C',
        wave: '#1C7293',
        coral: '#FF6B4A',
        safe: '#2A9D8F',
        warning: '#E63946',
      },
      boxShadow: {
        'soft': '0 1px 2px rgba(7,59,76,.05), 0 8px 24px rgba(7,59,76,.07)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
      }
    },
  },
  plugins: [],
}
