"use client";

/**
 * Inline role + scenario controls. A single horizontal line, dense.
 * Watch-for hint sits as a tail on the same flow so no vertical space
 * is wasted.
 */

import clsx from "clsx";
import { Eye } from "lucide-react";
import { useStore } from "@/lib/store";

export function Controls() {
  const {
    world,
    persona,
    scenario,
    setPersona,
    setScenario,
    run,
    status,
  } = useStore();

  const runAfter = (fn: () => void, carry = false) => {
    fn();
    setTimeout(() => run({ carryAsPrevious: carry }), 30);
  };

  return (
    <div className="space-y-2">
      {/* Two independent clusters. Each stays together — never orphans its
          label. On wide screens they sit side-by-side with a hairline
          divider; on narrow they stack cleanly. */}
      <div className="flex flex-col lg:flex-row lg:items-center gap-x-5 gap-y-2">
        <Cluster label="Role">
          {world.personas.map((p) => {
            const isActive = p.id === persona.id;
            return (
              <Pill
                key={p.id}
                active={isActive}
                disabled={status === "loading"}
                onClick={() =>
                  !isActive && runAfter(() => setPersona(p.id), true)
                }
              >
                {p.role}
              </Pill>
            );
          })}
        </Cluster>

        <div className="hidden lg:block h-5 w-px bg-hairline-strong shrink-0" />

        <Cluster label="Scenario">
          {world.scenarios.map((s) => {
            const isActive = s.id === scenario.id;
            return (
              <Pill
                key={s.id}
                active={isActive}
                onClick={() => !isActive && runAfter(() => setScenario(s.id))}
              >
                {s.title}
              </Pill>
            );
          })}
        </Cluster>
      </div>

      {/* Watch-for tail */}
      <div className="flex items-start gap-2 pt-1">
        <Eye size={12} className="text-muted mt-[3px] shrink-0" />
        <div className="text-label text-muted leading-snug">
          <span className="text-ink font-semibold">Watch for:</span>{" "}
          {scenario.watch_for}
        </div>
      </div>
    </div>
  );
}

function Cluster({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2.5 min-w-0">
      <div className="text-label uppercase tracking-[0.12em] text-muted font-semibold shrink-0">
        {label}
      </div>
      <div className="flex flex-wrap gap-1.5 min-w-0">{children}</div>
    </div>
  );
}

function Pill({
  active,
  disabled,
  onClick,
  children,
}: {
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        "px-2.5 py-1 border text-label transition-all",
        active
          ? "bg-ink text-canvas border-ink"
          : "bg-surface text-muted border-hairline hover:text-ink hover:border-ink disabled:opacity-50 disabled:cursor-not-allowed",
      )}
    >
      {children}
    </button>
  );
}
