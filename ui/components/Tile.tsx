"use client";

import clsx from "clsx";

/**
 * Framed content block with three visual pieces:
 *   1. Outer border (hairline)
 *   2. Tinted header strip (elevated fill) with label + optional right slot
 *   3. Body on surface (white on canvas, so tiles clearly pop)
 *
 * Tone cues the category:
 *   neutral — plain (most blocks)
 *   accent  — blue left bar + blue label (the DAG, the signature step)
 *   warn    — amber tint + amber label (tribal knowledge)
 *   danger  — red tint + red label (policy denials)
 */
export function Tile({
  label,
  tone = "neutral",
  right,
  children,
  className,
  padded = true,
}: {
  label?: string;
  tone?: "neutral" | "accent" | "warn" | "danger";
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  padded?: boolean;
}) {
  const borderCls = {
    neutral: "border-hairline dark:border-hairline-dark",
    accent:
      "border-hairline dark:border-hairline-dark border-l-[3px] border-l-accent",
    warn:
      "border-hairline dark:border-hairline-dark border-l-[3px] border-l-warn",
    danger:
      "border-hairline dark:border-hairline-dark border-l-[3px] border-l-danger",
  }[tone];

  const headerFill = {
    neutral: "bg-elevated dark:bg-elevated-dark",
    accent: "bg-accent-soft dark:bg-elevated-dark",
    warn: "bg-warn-soft dark:bg-elevated-dark",
    danger: "bg-danger-soft dark:bg-elevated-dark",
  }[tone];

  const headerLabelCls = {
    neutral: "text-muted",
    accent: "text-accent",
    warn: "text-warn",
    danger: "text-danger",
  }[tone];

  return (
    <section
      className={clsx(
        "border bg-surface dark:bg-surface-dark",
        borderCls,
        className,
      )}
    >
      {(label || right) && (
        <header
          className={clsx(
            "flex items-center justify-between px-5 py-2.5 border-b border-hairline dark:border-hairline-dark",
            headerFill,
          )}
        >
          {label && (
            <div
              className={clsx(
                "text-label uppercase tracking-[0.12em] font-semibold",
                headerLabelCls,
              )}
            >
              {label}
            </div>
          )}
          {right && <div>{right}</div>}
        </header>
      )}
      <div className={clsx(padded && "px-5 py-5")}>{children}</div>
    </section>
  );
}
