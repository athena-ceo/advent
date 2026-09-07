/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        serif: ["Georgia", "Cambria", "serif"],
      },
      colors: {
        cave: {
          900: "#14100c", 800: "#1d1712", 700: "#2a2119", 600: "#3a2e22",
          300: "#a99a80", 200: "#cabfa8", 100: "#e8e0d0",
        },
        amber: { glow: "#f5b642" },
      },
    },
  },
  plugins: [],
};
