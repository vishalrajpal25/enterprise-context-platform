"use client";

import type { ResolvedConcept } from "@/lib/types";

export function Meaning({
  concepts,
}: {
  concepts: Record<string, ResolvedConcept>;
}) {
  const entries = Object.entries(concepts);
  if (!entries.length) return null;
  return (
    <div>
      <div className="space-y-4">
        {entries.map(([key, c]) => (
          <div
            key={key}
            className="border-l-2 border-hairline dark:border-hairline-dark pl-4"
          >
            <div className="flex items-baseline gap-2">
              <div className="text-body font-medium">{c.canonical_name}</div>
              {c.department_variation && (
                <div className="text-label text-muted">
                  · {c.department_variation}
                </div>
              )}
            </div>
            <p className="mt-1 text-body text-muted">{c.plain_english}</p>
            {c.fiscal_resolution && (
              <div className="mt-1.5 text-label font-mono text-accent">
                {c.fiscal_resolution}
              </div>
            )}
            <div className="mt-1.5 text-label text-muted">
              Source: {c.source}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
