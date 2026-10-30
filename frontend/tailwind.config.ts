import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        nunito: ["Nunito", "ui-rounded", "SF Pro Rounded", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "var(--ink)",
        muted: "var(--muted)",
        card: "var(--card)",
      },
      borderRadius: {
        shell: "44px",
        sidebar: "36px",
        card: "28px",
        inner: "20px",
        badge: "18px",
      },
      boxShadow: {
        shell: "var(--sh-shell)",
        sidebar: "var(--sh-sidebar)",
        card: "var(--sh-card)",
        "card-hover": "var(--sh-card-hover)",
        tint: "var(--sh-tint)",
        btn: "var(--sh-btn)",
        "btn-light": "var(--sh-btn-light)",
        pill: "var(--sh-pill-active)",
        badge: "var(--sh-badge)",
        field: "var(--sh-field)",
      },
    },
  },
  plugins: [],
} satisfies Config;
