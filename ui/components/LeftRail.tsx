"use client";

/**
 * Navigator rail — two tiers only:
 *   Industry  →  Company
 *
 * Role and Scenario live in the canvas as interactive controls, since
 * swapping them is the core demo interaction and should be where the
 * user's attention already is.
 */

import clsx from "clsx";
import { useMemo } from "react";
import { useStore } from "@/lib/store";
import { INDUSTRIES, findIndustryForWorld } from "@/lib/worlds";

export function LeftRail() {
  const { world, setWorld, run } = useStore();

  const currentIndustry = useMemo(
    () => findIndustryForWorld(world.id),
    [world.id],
  );

  const runAfter = (fn: () => void) => {
    fn();
    setTimeout(() => run(), 30);
  };

  return (
    <aside className="w-rail shrink-0 overflow-y-auto border-r border-hairline dark:border-hairline-dark bg-elevated dark:bg-elevated-dark">
      {/* INDUSTRY */}
      <Section title="Industry">
        <ul>
          {INDUSTRIES.map((ind) => {
            const isActive = ind.id === currentIndustry.id;
            return (
              <li key={ind.id}>
                <button
                  onClick={() => {
                    if (!isActive) runAfter(() => setWorld(ind.worlds[0].id));
                  }}
                  className={clsx(
                    "w-full text-left px-5 py-2 text-body transition-colors border-l-[3px]",
                    isActive
                      ? "bg-surface dark:bg-surface-dark border-l-accent text-ink dark:text-ink-dark font-medium"
                      : "border-l-transparent text-muted hover:bg-surface/50 dark:hover:bg-surface-dark/50 hover:text-ink dark:hover:text-ink-dark",
                  )}
                >
                  {ind.name}
                </button>
              </li>
            );
          })}
        </ul>
      </Section>

      {/* COMPANY */}
      <Section title="Company">
        <ul>
          {currentIndustry.worlds.map((w) => {
            const isActive = w.id === world.id;
            return (
              <li key={w.id}>
                <button
                  onClick={() => !isActive && runAfter(() => setWorld(w.id))}
                  className={clsx(
                    "w-full text-left px-5 py-2 text-body transition-colors border-l-[3px]",
                    isActive
                      ? "bg-surface dark:bg-surface-dark border-l-accent text-ink dark:text-ink-dark font-medium"
                      : "border-l-transparent text-muted hover:bg-surface/50 dark:hover:bg-surface-dark/50 hover:text-ink dark:hover:text-ink-dark",
                  )}
                >
                  {w.name}
                </button>
              </li>
            );
          })}
        </ul>
      </Section>
    </aside>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border-b border-hairline-strong dark:border-hairline-dark py-2">
      <div className="px-5 pt-2 pb-1.5">
        <div className="text-label uppercase tracking-[0.14em] text-muted font-semibold">
          {title}
        </div>
      </div>
      {children}
    </section>
  );
}
