import type { Config } from "tailwindcss";

// Tailwind reads the CSS variables from tokens.css, so a colour is never hardcoded in a
// component - theme switching recolours everything from one place.
const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        app: "var(--bg-app)",
        panel: "var(--bg-panel)",
        "panel-alt": "var(--bg-panel-alt)",
        elevated: "var(--bg-elevated)",
        inset: "var(--bg-inset)",
        primary: "var(--text-primary)",
        secondary: "var(--text-secondary)",
        muted: "var(--text-muted)",
        inverse: "var(--text-inverse)",
        accent: "var(--text-accent)",
        "border-subtle": "var(--border-subtle)",
        "border-strong": "var(--border-strong)",
        interactive: "var(--interactive-primary)",
        "interactive-hover": "var(--interactive-primary-hover)",
        "price-up": "var(--price-up)",
        "price-up-bg": "var(--price-up-bg)",
        "price-down": "var(--price-down)",
        "price-down-bg": "var(--price-down-bg)",
        "price-flat": "var(--price-flat)",
        "sev-critical": "var(--sev-critical)",
        "sev-high": "var(--sev-high)",
        "sev-medium": "var(--sev-medium)",
        "sev-low": "var(--sev-low)",
        "quality-high": "var(--quality-high)",
        "quality-medium": "var(--quality-medium)",
        "quality-low": "var(--quality-low)",
        "mode-live": "var(--mode-live)",
        "mode-cached": "var(--mode-cached)",
        "mode-replay": "var(--mode-replay)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
      },
      maxWidth: { content: "1680px" },
    },
  },
  plugins: [],
};
export default config;
