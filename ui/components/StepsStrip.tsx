"use client";

/**
 * Thin one-line guidance strip between the topbar and the main layout.
 * Three inline numbered steps. Dismissable — remembered per-browser.
 */

import { useEffect, useState } from "react";
import { X } from "lucide-react";

const STEPS = [
  "Pick an industry and company",
  "Ask the pre-filled question",
  "Switch roles to see the answer change",
];

export function StepsStrip() {
  const [open, setOpen] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (localStorage.getItem("ecp-steps-dismissed") === "1") setOpen(false);
  }, []);

  const dismiss = () => {
    localStorage.setItem("ecp-steps-dismissed", "1");
    setOpen(false);
  };

  if (!open) return null;

  return (
    <div className="shrink-0 border-b border-hairline bg-elevated/60">
      <div className="flex items-center justify-between px-6 py-2">
        <ol className="flex items-center gap-5 text-label">
          {STEPS.map((step, i) => (
            <li key={i} className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-[18px] h-[18px] border border-accent text-accent font-mono font-semibold text-[10px]">
                {i + 1}
              </span>
              <span className="text-muted">{step}</span>
              {i < STEPS.length - 1 && (
                <span className="text-hairline-strong ml-3">→</span>
              )}
            </li>
          ))}
        </ol>
        <button
          onClick={dismiss}
          className="p-1 text-muted hover:text-ink transition-colors"
          aria-label="Dismiss"
        >
          <X size={13} />
        </button>
      </div>
    </div>
  );
}
