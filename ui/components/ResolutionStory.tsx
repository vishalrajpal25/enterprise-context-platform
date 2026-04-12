"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";
import { ArrowLeftRight, Users, ChevronDown } from "lucide-react";
import { useStore } from "@/lib/store";
import { DAG } from "./DAG";
import { ResolutionGraph } from "./ResolutionGraph";
import { SourceLineage } from "./SourceLineage";
import { Warnings } from "./Warnings";
import { Governance } from "./Governance";
import { Meaning } from "./Meaning";
import { Precedents } from "./Precedents";
import { Tile } from "./Tile";

export function ResolutionStory() {
  const {
    current,
    previous,
    previousPersonaId,
    status,
    error,
    persona,
    world,
    run,
    setPersona,
    clearComparison,
  } = useStore();

  if (status === "loading" && !current) return <Skeleton />;
  if (error && !current)
    return (
      <div className="border border-danger text-danger p-5">
        <div className="label mb-1">Error</div>
        {error}
      </div>
    );
  if (!current) return null;

  const contrast = world.personas.find((p) => p.id !== persona.id);
  const previousRole = previousPersonaId
    ? world.personas.find((p) => p.id === previousPersonaId)?.role
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
      className="space-y-6"
    >
      {/* ── Answer headline ────────────────────────────────────── */}
      <section className="bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark px-6 py-5">
        <div className="flex items-baseline justify-between gap-4 mb-2">
          <div className="text-label uppercase tracking-[0.14em] text-accent font-semibold">
            Resolved
          </div>
          <div className="flex items-center gap-3 text-label text-muted">
            <span className="font-semibold tabular-nums text-ink dark:text-ink-dark">
              {Math.round(current.confidence.overall * 100)}%
            </span>
            <span className="text-hairline-strong">·</span>
            <span className="tabular-nums">{current.latency_ms}ms</span>
            <span className="text-hairline-strong">·</span>
            <span className="font-mono text-[11px]">{current.resolution_id}</span>
          </div>
        </div>
        <h2 className="text-[17px] leading-[24px] font-medium text-ink dark:text-ink-dark">
          {current.headline}
        </h2>
      </section>

      {/* ── Resolution flow — full width ────────────────────── */}
      {current.resolution_dag.length > 0 && (
        <Tile tone="accent" label="Resolution flow" right={
          <span className="text-[12px] font-mono text-muted tabular-nums">
            {current.resolution_dag.length} steps
          </span>
        }>
          <ResolutionGraph steps={current.resolution_dag} />
        </Tile>
      )}

      {/* ── Meaning + warnings — two column ─────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-6">
        <Tile label="Meaning">
          <Meaning concepts={current.resolved_concepts} />
        </Tile>
        {current.warnings.length > 0 && (
          <Tile
            tone="warn"
            label={`Tribal knowledge · ${current.warnings.length}`}
          >
            <Warnings warnings={current.warnings} />
          </Tile>
        )}
      </div>

      {/* ── Source lineage ───────────────────────────────────── */}
      {current.execution_plan.length > 0 && (
        <Tile label="Source lineage">
          <SourceLineage plan={current.execution_plan} />
        </Tile>
      )}

      {/* ── Decision trace (collapsible) ────────────────────── */}
      <DetailSection label={`Decision trace · ${current.resolution_dag.length} steps`}>
        <DAG steps={current.resolution_dag} />
      </DetailSection>

      {/* ── Governance + precedents ──────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Tile
          tone={current.access_granted ? "neutral" : "danger"}
          label="Governance"
        >
          <Governance
            access_granted={current.access_granted}
            policies={current.policies_evaluated}
            filtered={current.filtered_concepts}
          />
        </Tile>
        {current.precedents_used.length > 0 && (
          <Tile label={`Precedents · ${current.precedents_used.length}`}>
            <Precedents precedents={current.precedents_used} />
          </Tile>
        )}
      </div>

      {/* Aha nudge */}
      {contrast && !previous && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
        >
          <div className="border border-dashed border-hairline dark:border-hairline-dark p-5 flex items-center gap-4">
            <Users size={18} className="text-muted shrink-0" />
            <div className="flex-1">
              <div className="text-body">
                Now try the same question as a{" "}
                <span className="font-medium">{contrast.role}</span>.
              </div>
              <div className="text-label text-muted mt-0.5">
                Watch the definition change. This is the whole point.
              </div>
            </div>
            <button
              onClick={async () => {
                setPersona(contrast.id);
                setTimeout(() => run({ carryAsPrevious: true }), 30);
              }}
              className="btn btn-accent"
            >
              Switch to {contrast.role}
              <ArrowLeftRight size={14} />
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

function DetailSection({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <section className="border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-subtle dark:hover:bg-subtle-dark transition-colors"
      >
        <span className="text-label uppercase tracking-[0.12em] font-semibold text-muted">
          {label}
        </span>
        <ChevronDown
          size={16}
          className={clsx(
            "text-muted transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {open && <div className="px-5 pb-5">{children}</div>}
    </section>
  );
}

function Skeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-subtle dark:bg-subtle-dark w-3/4" />
      <div className="h-4 bg-subtle dark:bg-subtle-dark w-1/2" />
      <div className="h-40 bg-subtle dark:bg-subtle-dark" />
      <div className="grid grid-cols-2 gap-6">
        <div className="h-56 bg-subtle dark:bg-subtle-dark" />
        <div className="h-56 bg-subtle dark:bg-subtle-dark" />
      </div>
    </div>
  );
}
