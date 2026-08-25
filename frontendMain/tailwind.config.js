/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        vgimt: {
           header: '#014f86', // User requested blue
           neutral: '#f8fafc',
           accent: '#014f86', // Matching accent
           input: '#f1f5f9',
           text: '#334155',
        }
      }
    },
  },
  plugins: [],
}
