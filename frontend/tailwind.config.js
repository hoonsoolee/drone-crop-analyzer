/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2d6a4f',
          light: '#52b788',
          dark: '#1b4332',
        },
      },
    },
  },
  plugins: [],
}
