import type { Config } from "tailwindcss";

/**
 * ECP Studio — "Graphite" design tokens.
 *
 * Monochrome-forward. Single restrained accent (electric blue) used sparingly
 * for active states, focus cues, and the currently-animating DAG node.
 * Warnings = amber. Errors = red. Everything else = greyscale.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ── Layered surface hierarchy ────────────────────────────────
        // canvas   — the page background (coolest, recedes)
        // surface  — panels sitting ON canvas (warmer, catches the eye)
        // elevated — inset blocks, tile headers, hover states
        // ink      — primary text
        canvas: {
          DEFAULT: "#F4F3EE", // warm off-white, slightly ivory
          dark: "#0A0A0A",
        },
        surface: {
          DEFAULT: "#FFFFFF", // crisp white tiles pop against canvas
          dark: "#141414",
        },
        elevated: {
          DEFAULT: "#F7F6F1", // header strips, inset blocks
          dark: "#1C1C1C",
        },
        ink: {
          DEFAULT: "#111111",
          light: "#3F3F3F", // secondary ink — darker than muted
          dark: "#F5F5F5",
        },
        // Hairlines
        hairline: {
          DEFAULT: "#E2DFD6", // warmer than pure gray so tiles feel ledger-like
          strong: "#C9C5B8",
          dark: "#262626",
        },
        muted: {
          DEFAULT: "#737064",
          dark: "#8A8A8A",
        },
        subtle: {
          DEFAULT: "#EDEBE3",
          dark: "#1A1A1A",
        },
        // ── Accent ──────────────────────────────────────────────────
        accent: {
          DEFAULT: "#1F4DD8", // slightly deeper blue, reads as ink+intent
          hover: "#1A3FB5",
          soft: "#E8EDFC",
        },
        // ── Semantic ────────────────────────────────────────────────
        warn: {
          DEFAULT: "#A1601C",
          soft: "#FBF3E6",
        },
        danger: {
          DEFAULT: "#B91C1C",
          soft: "#FCEBEB",
        },
        ok: {
          DEFAULT: "#166A3E",
          soft: "#E6F1EA",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "system-ui",
          "sans-serif",
        ],
        mono: [
          "IBM Plex Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
      fontSize: {
        // Four sizes, no more.
        hero: ["32px", { lineHeight: "40px", letterSpacing: "-0.02em" }],
        title: ["20px", { lineHeight: "28px", letterSpacing: "-0.01em" }],
        body: ["14px", { lineHeight: "22px" }],
        label: ["12px", { lineHeight: "16px", letterSpacing: "0.02em" }],
      },
      borderRadius: {
        none: "0",
        sm: "2px",
        DEFAULT: "4px",
        md: "6px",
      },
      spacing: {
        rail: "280px",
      },
    },
  },
  plugins: [],
};

export default config;
