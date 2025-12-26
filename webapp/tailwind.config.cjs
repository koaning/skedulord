module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"] ,
  theme: {
    extend: {
      fontFamily: {
        display: ["'Space Grotesk'", "ui-sans-serif", "system-ui"],
        body: ["'IBM Plex Sans'", "ui-sans-serif", "system-ui"]
      },
      colors: {
        ink: "#14151a",
        haze: "#f6f4ef",
        sand: "#f0e8dc",
        clay: "#c9b7a7",
        accent: "#ff7a00",
        plum: "#5e3f6b"
      },
      boxShadow: {
        soft: "0 20px 60px rgba(20, 21, 26, 0.12)",
        card: "0 12px 40px rgba(20, 21, 26, 0.08)"
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};
