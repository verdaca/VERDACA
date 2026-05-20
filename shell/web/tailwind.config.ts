import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Forest + Midnight palette per arch §2.1
        primary: "#1B4332",
        secondary: "#0D1B2A",
        accent: "#52B788",
        background: "#FAFAF9",
        foreground: "#1A1A1A",
        muted: "#6B7280",
        error: "#DC2626",
        success: "#059669",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
