import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0c",
        surface: "#111114",
        border: "#232328",
        foreground: "#e6e6e9",
        muted: "#8a8a92",
        accent: "#5b8def",
        danger: "#e5484d",
        warning: "#e5a63d",
        success: "#3dd68c",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
