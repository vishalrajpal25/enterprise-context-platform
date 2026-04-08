"use client";

import { motion } from "framer-motion";
import clsx from "clsx";

/**
 * A single SVG ring showing overall confidence. Color shifts only at
 * thresholds (ok: ≥0.85, warn: ≥0.7, danger: <0.7). Animates from 0 on
 * mount so the user sees it fill.
 */
export function ConfidenceRing({
  value,
  size = 120,
  label = "Confidence",
}: {
  value: number; // 0..1
  size?: number;
  label?: string;
}) {
  const clamped = Math.max(0, Math.min(1, value));
  const stroke = 8;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - clamped);

  const state: "ok" | "warn" | "danger" =
    clamped >= 0.85 ? "ok" : clamped >= 0.7 ? "warn" : "danger";

  const ringColor =
    state === "ok"
      ? "stroke-ok"
      : state === "warn"
      ? "stroke-warn"
      : "stroke-danger";

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          strokeWidth={stroke}
          className="stroke-hairline dark:stroke-hairline-dark"
          fill="none"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          strokeWidth={stroke}
          className={clsx(ringColor, "fill-none")}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.1, ease: [0.2, 0.8, 0.2, 1] }}
          fill="none"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-title font-semibold tabular-nums">
          {Math.round(clamped * 100)}
        </div>
        <div className="label mt-0.5">{label}</div>
      </div>
    </div>
  );
}
