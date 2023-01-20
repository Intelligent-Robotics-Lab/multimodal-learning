/* eslint-env node */
const colors = require("tailwindcss/colors");

module.exports = {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  safelist: [
    {
      pattern: /(bg|text)-(red|purple|teal|gray)-(50|200|800)/,
    },
  ],
  theme: {
  },
  plugins: [],
};
