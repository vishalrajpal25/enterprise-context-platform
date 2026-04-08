"use client";

import { motion } from "framer-motion";
import { ArrowLeftRight, Users } from "lucide-react";
import { useStore } from "@/lib/store";
import { ConfidenceRing } from "./ConfidenceRing";
import { DAG } from "./DAG";
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
      {/* Headline — no tile, this is the hero */}
      <section className="bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark px-7 py-7">
        <div className="text-label uppercase tracking-[0.14em] text-accent font-semibold mb-3">
          Answer
        </div>
        <div className="flex items-start gap-8">
          <div className="flex-1 min-w-0">
            <h2 className="serif text-[34px] leading-[42px] font-semibold tracking-tight text-ink dark:text-ink-dark">
              {current.headline}
            </h2>
            <div className="mt-4 flex items-center gap-3 text-label">
              <span className="text-muted">
                Resolved in{" "}
                <span className="text-ink dark:text-ink-dark tabular-nums font-semibold">
                  {current.latency_ms}ms
                </span>
              </span>
              <span className="text-hairline-strong">·</span>
              <span className="mono text-muted">{current.resolution_id}</span>
            </div>
          </div>
          <ConfidenceRing
            value={current.confidence.overall}
            label="confidence"
          />
        </div>
      </section>

      {/* Comparison ribbon */}
      {previous && previousRole && (
        <Tile tone="accent" label="Same question · different answer">
          <div className="flex items-start gap-3">
            <ArrowLeftRight
              size={16}
              className="text-accent mt-1 shrink-0"
            />
            <div className="flex-1 text-body">
              <div className="text-muted">
                As{" "}
                <span className="text-ink dark:text-ink-dark font-medium">
                  {previousRole}
                </span>
                : {previous.headline}
              </div>
              <div className="mt-1.5 text-muted">
                As{" "}
                <span className="text-ink dark:text-ink-dark font-medium">
                  {persona.role}
                </span>
                : {current.headline}
              </div>
              <div className="mt-3 text-label text-muted">
                The question didn&apos;t change. The context did.
              </div>
            </div>
            <button
              onClick={clearComparison}
              className="text-label text-muted hover:text-ink dark:hover:text-ink-dark"
            >
              dismiss
            </button>
          </div>
        </Tile>
      )}

      {/* DAG — its own tile, accent-cued (this is the signature moment) */}
      <Tile tone="accent" label="Decision flow">
        <DAG steps={current.resolution_dag} />
      </Tile>

      {/* Two-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.45fr_1fr] gap-6">
        <div className="space-y-6">
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
        <div className="space-y-6">
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
            <Tile
              label={`Precedents · ${current.precedents_used.length}`}
            >
              <Precedents precedents={current.precedents_used} />
            </Tile>
          )}
        </div>
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
