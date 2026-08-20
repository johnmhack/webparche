/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        parche: {
          bg: '#0a0f1e',
          card: '#111827',
          border: '#1e293b',
          cyan: '#22d3ee',
          green: '#34d399',
          pink: '#f472b6',
          muted: '#94a3b8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 40px -12px rgba(34, 211, 238, 0.35)',
      },
    },
  },
  plugins: [],
};
