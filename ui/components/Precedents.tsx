"use client";

import { Check, X } from "lucide-react";
import clsx from "clsx";
import type { Precedent } from "@/lib/types";

export function Precedents({ precedents }: { precedents: Precedent[] }) {
  return (
    <div>
      <div className="space-y-2">
        {precedents.map((p) => (
          <div
            key={p.resolution_id}
            className="flex items-start gap-3 text-body"
          >
            <div
              className={clsx(
                "shrink-0 w-4 h-4 mt-0.5 flex items-center justify-center border",
                p.feedback === "accepted"
                  ? "border-ok text-ok"
                  : p.feedback === "rejected"
                  ? "border-danger text-danger"
                  : "border-hairline dark:border-hairline-dark text-muted",
              )}
            >
              {p.feedback === "accepted" ? (
                <Check size={10} />
              ) : p.feedback === "rejected" ? (
                <X size={10} />
              ) : null}
            </div>
            <div className="flex-1 min-w-0">
              <div className="truncate">{p.query}</div>
              <div className="text-label text-muted">
                {p.user} · similarity{" "}
                <span className="tabular-nums">
                  {(p.similarity * 100).toFixed(0)}
                </span>
                %
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
