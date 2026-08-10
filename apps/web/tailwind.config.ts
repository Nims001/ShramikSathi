import type { Config } from "tailwindcss";

// ShramikSathi design system — calm, official, government-service look.
// Primary #1F75E6; light blue #E6F0FB highlights; #F8FAFC page background.

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#E6F0FB",
          100: "#D3E5F8",
          200: "#ADCBF2",
          300: "#87B1EC",
          400: "#5393E6",
          500: "#1F75E6",
          600: "#1B66C9",
          700: "#1753A8",
          800: "#134186",
          900: "#0F3064",
          950: "#0B2349",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-inter)",
          "Inter",
          "Roboto",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
      },
      boxShadow: {
        soft: "0 1px 2px rgb(16 24 40 / 0.04), 0 2px 6px rgb(16 24 40 / 0.06)",
        "soft-lg": "0 2px 4px rgb(16 24 40 / 0.05), 0 8px 24px rgb(16 24 40 / 0.08)",
      },
      borderRadius: {
        card: "18px",
      },
    },
  },
  plugins: [],
};

export default config;
