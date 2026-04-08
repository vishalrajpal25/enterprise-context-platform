"use client";

import { Lock, ShieldCheck } from "lucide-react";
import clsx from "clsx";

export function Governance({
  access_granted,
  policies,
  filtered,
}: {
  access_granted: boolean;
  policies: string[];
  filtered: string[];
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <div
          className={clsx(
            "inline-flex items-center gap-1.5 px-2 py-1 text-label border",
            access_granted
              ? "border-ok text-ok"
              : "border-danger text-danger",
          )}
        >
          {access_granted ? (
            <ShieldCheck size={12} />
          ) : (
            <Lock size={12} />
          )}
          {access_granted ? "access granted" : "access denied"}
        </div>
      </div>

      {policies.length > 0 && (
        <div className="mb-3">
          <div className="text-label text-muted mb-1.5">
            Policies evaluated
          </div>
          <div className="flex flex-wrap gap-1.5">
            {policies.map((p) => (
              <code
                key={p}
                className="text-label font-mono px-1.5 py-0.5 bg-subtle dark:bg-subtle-dark text-muted"
              >
                {p}
              </code>
            ))}
          </div>
        </div>
      )}

      {filtered.length > 0 && (
        <div>
          <div className="text-label text-muted mb-1.5">Filtered fields</div>
          <div className="flex flex-wrap gap-1.5">
            {filtered.map((f) => (
              <code
                key={f}
                className="text-label font-mono px-1.5 py-0.5 bg-subtle dark:bg-subtle-dark text-warn"
              >
                {f}
              </code>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
