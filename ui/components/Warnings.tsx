"use client";

import { AlertTriangle, Info, ShieldAlert } from "lucide-react";
import clsx from "clsx";
import type { TribalWarning } from "@/lib/types";
import { useState } from "react";

const ICON = {
  info: Info,
  warn: AlertTriangle,
  critical: ShieldAlert,
};

const TONE = {
  info: "border-hairline dark:border-hairline-dark text-muted",
  warn: "border-warn text-warn",
  critical: "border-danger text-danger",
};

export function Warnings({ warnings }: { warnings: TribalWarning[] }) {
  if (!warnings.length) return null;
  return (
    <div className="space-y-3">
      {warnings.map((w) => (
        <Warning key={w.id} w={w} />
      ))}
    </div>
  );
}

function Warning({ w }: { w: TribalWarning }) {
  const [open, setOpen] = useState(false);
  const Icon = ICON[w.severity] ?? Info;
  return (
    <button
      onClick={() => setOpen((o) => !o)}
      className={clsx(
        "block w-full text-left border-l-2 pl-4 pr-3 py-3",
        "hover:bg-subtle dark:hover:bg-subtle-dark transition-colors",
        TONE[w.severity],
      )}
    >
      <div className="flex items-start gap-3">
        <Icon size={16} className="mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-body font-medium text-ink dark:text-ink-dark">
            {w.headline}
          </div>
          {open && (
            <div className="mt-2 text-body text-muted">
              <p>{w.detail}</p>
              {(w.author || w.captured_at) && (
                <div className="mt-2 text-label">
                  {w.author}
                  {w.captured_at ? ` · ${w.captured_at}` : ""}
                </div>
              )}
            </div>
          )}
          {!open && (
            <div className="text-label text-muted mt-0.5">
              Click to expand
            </div>
          )}
        </div>
      </div>
    </button>
  );
}
