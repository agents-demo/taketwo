/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0b0f",
        surface: "#15151d",
        line: "#26262f",
        accent: "#7c3aed",
        accent2: "#a78bfa",
        good: "#34d399",
        bad: "#fb7185",
      },
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
