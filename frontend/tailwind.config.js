/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        fintech: {
          dark: "#0a1628",
          card: "#0f2038",
          border: "#1e3452",
          accent: "#00d4aa",
          accentHover: "#00b894",
          muted: "#8fa3bf",
          gold: "#f59e0b",
        },
      },
    },
  },
  plugins: [],
};
