"use client";

/**
 * The decision-flow transparency tile.
 *
 * Top:    a compact horizontal pill row — every step's icon + short label,
 *         acts as a scrubber and an overview at a glance.
 * Below:  a full vertical trace where each step renders its real
 *         source / query / found / selected — the audience sees exactly
 *         which store was hit and what came back.
 *
 * The whole point of ECP is transparency of meaning-resolution, so this
 * tile shows it rather than summarising it.
 */

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";
import type { ResolutionDAGStep, TraceIO } from "@/lib/types";
import type { LucideIcon } from "lucide-react";
import {
  Brain,
  Search,
  Calendar,
  ShieldCheck,
  MessageSquareWarning,
  Gauge,
  History,
  Layers,
  Database,
  Filter,
  DollarSign,
  BookOpen,
  Clock,
  FileCode,
  ChevronRight,
} from "lucide-react";

const ICON: Record<string, LucideIcon> = {
  parse_intent: Brain,
  find_concept: Search,
  apply_fiscal_calendar: Calendar,
  apply_temporal: Calendar,
  check_policy: ShieldCheck,
  lookup_tribal: MessageSquareWarning,
  score_confidence: Gauge,
  retrieve_precedents: History,
  resolve_portfolio: Layers,
  apply_overrides: BookOpen,
  resolve_peers: Layers,
  check_vintage: Clock,
  apply_fx: DollarSign,
  resolve_cohort: Layers,
  check_completion: Gauge,
  check_risk_adj: Gauge,
  apply_exclusions: Filter,
  redact_outputs: Filter,
  build_query: FileCode,
};

export function DAG({ steps }: { steps: ResolutionDAGStep[] }) {
  const [focused, setFocused] = useState<string | null>(null);
  const rowRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Reset focus when steps change (new resolution).
  useEffect(() => {
    setFocused(null);
  }, [steps]);

  if (!steps.length) return null;

  const onFocus = (id: string) => {
    setFocused(id);
    const el = rowRefs.current[id];
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  return (
    <div>
      {/* ── SCRUBBER ROW ────────────────────────────────────────────── */}
      <ol className="flex items-center flex-wrap gap-1.5 mb-6">
        {steps.map((step, i) => {
          const Icon = ICON[step.action] || Database;
          const isFocused = focused === step.id;
          return (
            <motion.li
              key={step.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.3 }}
              className="flex items-center"
            >
              <button
                onClick={() => onFocus(step.id)}
                className={clsx(
                  "group inline-flex items-center gap-1.5 px-2 py-1 border transition-all",
                  "text-label",
                  isFocused
                    ? "bg-accent text-white border-accent"
                    : "border-hairline text-muted hover:text-ink hover:border-ink",
                )}
              >
                <Icon size={12} />
                <span className="font-medium">{step.label}</span>
              </button>
              {i < steps.length - 1 && (
                <ChevronRight
                  size={12}
                  className="text-hairline-strong mx-0.5"
                />
              )}
            </motion.li>
          );
        })}
      </ol>

      {/* ── VERTICAL TRACE ──────────────────────────────────────────── */}
      <div className="relative">
        {/* The flow line */}
        <div className="absolute left-[19px] top-2 bottom-2 w-px bg-hairline" />

        <ol className="space-y-4">
          {steps.map((step, i) => (
            <TraceRow
              key={step.id}
              step={step}
              index={i}
              isFocused={focused === step.id}
              onFocus={() => onFocus(step.id)}
              registerRef={(el) => (rowRefs.current[step.id] = el)}
            />
          ))}
        </ol>
      </div>
    </div>
  );
}

function TraceRow({
  step,
  index,
  isFocused,
  onFocus,
  registerRef,
}: {
  step: ResolutionDAGStep;
  index: number;
  isFocused: boolean;
  onFocus: () => void;
  registerRef: (el: HTMLDivElement | null) => void;
}) {
  const Icon = ICON[step.action] || Database;

  return (
    <motion.div
      ref={registerRef}
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08 + 0.1, duration: 0.35 }}
      className="relative flex items-start gap-4 pl-0"
    >
      {/* Node marker */}
      <button
        onClick={onFocus}
        className={clsx(
          "relative z-10 shrink-0 w-10 h-10 flex items-center justify-center border bg-surface transition-colors",
          isFocused
            ? "border-accent text-accent ring-2 ring-accent/20"
            : "border-hairline-strong text-muted hover:text-ink hover:border-ink",
        )}
      >
        <Icon size={16} />
      </button>

      {/* Step body */}
      <div
        className={clsx(
          "flex-1 min-w-0 border bg-surface transition-all",
          isFocused
            ? "border-accent shadow-[0_0_0_1px_#1F4DD8]"
            : "border-hairline",
        )}
      >
        {/* Row header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-hairline bg-elevated">
          <div className="flex items-baseline gap-2">
            <span className="text-label font-mono text-muted">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="text-body font-medium text-ink">
              {step.label}
            </span>
          </div>
          <span className="text-label font-mono text-muted tabular-nums">
            {step.duration_ms}ms
          </span>
        </div>

        {/* Description line */}
        <div className="px-4 pt-3 pb-2 text-label text-muted">
          {step.description}
        </div>

        {/* I/O panel */}
        {step.io && <IOPanel io={step.io} />}
      </div>
    </motion.div>
  );
}

function IOPanel({ io }: { io: TraceIO }) {
  return (
    <div className="px-4 pb-3 space-y-2.5">
      {/* Source */}
      <Line label="source" value={io.source} mono />

      {/* Query (if present) */}
      {io.query && (
        <div>
          <div className="text-label uppercase tracking-wider text-muted font-semibold mb-1">
            query
          </div>
          <pre className="text-label font-mono text-ink bg-elevated border border-hairline px-3 py-2 whitespace-pre-wrap break-all">
            {io.query}
          </pre>
        </div>
      )}

      {/* Found candidates */}
      {io.found && io.found.length > 0 && (
        <div>
          <div className="text-label uppercase tracking-wider text-muted font-semibold mb-1">
            returned · {io.found.length}
          </div>
          <ul className="border border-hairline bg-elevated divide-y divide-hairline">
            {io.found.map((f, i) => (
              <li
                key={i}
                className="px-3 py-1.5 text-label font-mono text-ink"
              >
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Structured output */}
      {io.output && (
        <div>
          <div className="text-label uppercase tracking-wider text-muted font-semibold mb-1">
            output
          </div>
          <dl className="border border-hairline bg-elevated">
            {Object.entries(io.output).map(([k, v], i, arr) => (
              <div
                key={k}
                className={clsx(
                  "flex items-baseline gap-3 px-3 py-1.5",
                  i < arr.length - 1 && "border-b border-hairline",
                )}
              >
                <dt className="text-label uppercase tracking-wider text-muted font-semibold w-32 shrink-0">
                  {k.replace(/_/g, " ")}
                </dt>
                <dd className="text-label font-mono text-ink">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {/* Selected / conclusion */}
      {io.selected && (
        <div className="flex items-start gap-2 pt-1">
          <ChevronRight
            size={12}
            className="text-accent mt-[3px] shrink-0"
          />
          <div className="text-label font-mono text-accent flex-1 break-words">
            {io.selected}
          </div>
        </div>
      )}
    </div>
  );
}

function Line({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-baseline gap-3">
      <span className="text-label uppercase tracking-wider text-muted font-semibold w-16 shrink-0">
        {label}
      </span>
      <span
        className={clsx(
          "text-label flex-1 break-words",
          mono ? "font-mono text-ink" : "text-ink",
        )}
      >
        {value}
      </span>
    </div>
  );
}
