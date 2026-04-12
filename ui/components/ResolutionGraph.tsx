"use client";

/**
 * Resolution flow — animated visualization showing how the engine
 * traverses stores to resolve a query.
 *
 * Top:    QUERY → [store] → [store] → … → RESOLVED (horizontal)
 * Bottom: Incremental trace log — each step stays visible as it
 *         appears, building a complete audit trail.
 *
 * Clicking a store icon filters the trace to only its steps.
 */

import { useEffect, useState, useMemo, useRef } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";
import type { ResolutionDAGStep } from "@/lib/types";
import {
  Brain,
  Database,
  Search,
  ShieldCheck,
  MessageSquareWarning,
  History,
  Layers,
  ChevronRight,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

// ─── Store definitions ──────────────────────────────────────────────

type StoreNode = {
  id: string;
  label: string;
  icon: LucideIcon;
  bg: string;
  activeBg: string;
  dotColor: string;
  actions: string[];
};

const STORES: StoreNode[] = [
  {
    id: "intent",
    label: "Intent Parser",
    icon: Brain,
    bg: "bg-purple-50 text-purple-300 border-purple-100",
    activeBg: "bg-purple-600 text-white border-purple-600 shadow-lg shadow-purple-200",
    dotColor: "bg-purple-500",
    actions: ["parse_intent"],
  },
  {
    id: "graph",
    label: "Knowledge Graph",
    icon: Database,
    bg: "bg-blue-50 text-blue-300 border-blue-100",
    activeBg: "bg-blue-600 text-white border-blue-600 shadow-lg shadow-blue-200",
    dotColor: "bg-blue-500",
    actions: [
      "find_concept", "resolve_metric", "resolve_dimension",
      "resolve_scope", "resolve_adjustment", "resolve_portfolio",
      "resolve_peers", "resolve_cohort",
    ],
  },
  {
    id: "vector",
    label: "Vector Store",
    icon: Search,
    bg: "bg-emerald-50 text-emerald-300 border-emerald-100",
    activeBg: "bg-emerald-600 text-white border-emerald-600 shadow-lg shadow-emerald-200",
    dotColor: "bg-emerald-500",
    actions: ["retrieve_precedents", "find_precedents"],
  },
  {
    id: "tribal",
    label: "Tribal Knowledge",
    icon: MessageSquareWarning,
    bg: "bg-amber-50 text-amber-300 border-amber-100",
    activeBg: "bg-amber-500 text-white border-amber-500 shadow-lg shadow-amber-200",
    dotColor: "bg-amber-500",
    actions: ["check_tribal_knowledge", "lookup_tribal", "check_vintage", "apply_overrides"],
  },
  {
    id: "policy",
    label: "Policy Engine",
    icon: ShieldCheck,
    bg: "bg-red-50 text-red-300 border-red-100",
    activeBg: "bg-red-600 text-white border-red-600 shadow-lg shadow-red-200",
    dotColor: "bg-red-500",
    actions: ["check_policy", "authorize", "apply_exclusions", "redact_outputs"],
  },
  {
    id: "semantic",
    label: "Semantic Layer",
    icon: Layers,
    bg: "bg-cyan-50 text-cyan-300 border-cyan-100",
    activeBg: "bg-cyan-600 text-white border-cyan-600 shadow-lg shadow-cyan-200",
    dotColor: "bg-cyan-500",
    actions: ["build_query", "apply_fiscal_calendar", "apply_temporal", "apply_fx", "resolve_time"],
  },
  {
    id: "trace",
    label: "Decision Trace",
    icon: History,
    bg: "bg-slate-50 text-slate-300 border-slate-200",
    activeBg: "bg-slate-700 text-white border-slate-700 shadow-lg shadow-slate-200",
    dotColor: "bg-slate-500",
    actions: ["score_confidence", "check_completion", "check_risk_adj"],
  },
];

function storeForAction(action: string): StoreNode | undefined {
  return STORES.find((s) => s.actions.includes(action));
}

// ─── Component ──────────────────────────────────────────────────────

export function ResolutionGraph({ steps }: { steps: ResolutionDAGStep[] }) {
  // How many steps have been revealed so far (animation frontier)
  const [revealedCount, setRevealedCount] = useState(0);
  // Which store the user clicked to filter (null = show all revealed)
  const [selectedStore, setSelectedStore] = useState<string | null>(null);
  const traceEndRef = useRef<HTMLDivElement>(null);

  // Which stores were actually used, in order of first appearance
  const usedStores = useMemo(() => {
    const seen: string[] = [];
    for (const step of steps) {
      const store = storeForAction(step.action);
      if (store && !seen.includes(store.id)) seen.push(store.id);
    }
    return seen.map((id) => STORES.find((s) => s.id === id)!);
  }, [steps]);

  // Map each step index → store index
  const stepToStore = useMemo(() => {
    return steps.map((step) => {
      const store = storeForAction(step.action);
      if (!store) return -1;
      return usedStores.findIndex((s) => s.id === store.id);
    });
  }, [steps, usedStores]);

  // Map each step index → store node
  const stepToStoreNode = useMemo(() => {
    return steps.map((step) => storeForAction(step.action) ?? null);
  }, [steps]);

  // Animate: reveal one step at a time
  useEffect(() => {
    if (steps.length === 0) return;
    setRevealedCount(0);
    setSelectedStore(null);
    let i = 0;
    const timer = setInterval(() => {
      i++;
      if (i > steps.length) {
        clearInterval(timer);
        return;
      }
      setRevealedCount(i);
    }, 450);
    return () => clearInterval(timer);
  }, [steps]);

  // Auto-scroll trace log to bottom as new steps appear
  useEffect(() => {
    traceEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [revealedCount]);

  const done = revealedCount >= steps.length;

  // Which store indices have at least one revealed step
  const activeStoreIndices = useMemo(() => {
    const set = new Set<number>();
    for (let i = 0; i < revealedCount && i < stepToStore.length; i++) {
      if (stepToStore[i] >= 0) set.add(stepToStore[i]);
    }
    return set;
  }, [revealedCount, stepToStore]);

  // The store index that is currently being animated (latest revealed step's store)
  const animatingStoreIdx = revealedCount > 0 && revealedCount <= steps.length
    ? stepToStore[revealedCount - 1]
    : -1;

  // Durations per store (only counting revealed steps)
  const storeDurations = useMemo(() => {
    const d: number[] = new Array(usedStores.length).fill(0);
    for (let i = 0; i < revealedCount && i < steps.length; i++) {
      const si = stepToStore[i];
      if (si >= 0) d[si] += steps[i].duration_ms;
    }
    return d;
  }, [revealedCount, steps, stepToStore, usedStores.length]);

  // Steps to show in the trace log
  const visibleSteps = useMemo(() => {
    const revealed = steps.slice(0, revealedCount);
    if (!selectedStore) return revealed.map((s, i) => ({ step: s, idx: i }));
    return revealed
      .map((s, i) => ({ step: s, idx: i }))
      .filter(({ step }) => {
        const store = storeForAction(step.action);
        return store?.id === selectedStore;
      });
  }, [steps, revealedCount, selectedStore]);

  function handleStoreClick(store: StoreNode) {
    if (selectedStore === store.id) {
      setSelectedStore(null); // toggle off
    } else {
      setSelectedStore(store.id);
    }
  }

  return (
    <div className="space-y-5">
      {/* ── Horizontal store flow ─────────────────────────────── */}
      <div className="flex items-center gap-0 overflow-x-auto py-2">
        {/* QUERY pill */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="shrink-0 px-4 py-2 bg-accent text-white text-[13px] font-semibold tracking-wide rounded"
        >
          QUERY
        </motion.div>

        {usedStores.map((store, i) => {
          const Icon = store.icon;
          const isActive = activeStoreIndices.has(i);
          const isAnimating = animatingStoreIdx === i && !done;
          const isSelected = selectedStore === store.id;

          return (
            <div key={store.id} className="flex items-center shrink-0">
              {/* Connector */}
              <motion.div
                className="h-[2px] w-8 mx-1"
                initial={{ scaleX: 0, opacity: 0 }}
                animate={{
                  scaleX: isActive ? 1 : 0.3,
                  opacity: isActive ? 1 : 0.15,
                  backgroundColor: isActive ? "#1F4DD8" : "#ddd",
                }}
                transition={{ duration: 0.4, delay: i * 0.06 }}
                style={{ originX: 0 }}
              />

              {/* Store node — clickable */}
              <motion.button
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 + 0.1, duration: 0.3 }}
                onClick={() => isActive && handleStoreClick(store)}
                className={clsx(
                  "flex flex-col items-center gap-1.5 shrink-0 group",
                  isActive ? "cursor-pointer" : "cursor-default",
                )}
              >
                <div
                  className={clsx(
                    "w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                    isActive ? store.activeBg : store.bg,
                    isAnimating && "ring-4 ring-accent/25 scale-110",
                    isSelected && "ring-4 ring-ink/20 scale-110",
                    isActive && !isAnimating && !isSelected && "group-hover:scale-105 group-hover:ring-2 group-hover:ring-ink/10",
                  )}
                >
                  <Icon size={20} />
                </div>
                <div className="text-center">
                  <div
                    className={clsx(
                      "text-[11px] font-semibold leading-tight whitespace-nowrap transition-colors duration-300",
                      isSelected ? "text-ink underline underline-offset-2" : isActive ? "text-ink" : "text-muted/40",
                    )}
                  >
                    {store.label}
                  </div>
                  {isActive && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-[10px] font-mono text-muted mt-0.5 tabular-nums"
                    >
                      {Math.round(storeDurations[i])}ms
                    </motion.div>
                  )}
                </div>
              </motion.button>
            </div>
          );
        })}

        {/* Final connector */}
        <motion.div
          className="h-[2px] w-8 mx-1 shrink-0"
          initial={{ scaleX: 0 }}
          animate={{
            scaleX: done ? 1 : 0.3,
            opacity: done ? 1 : 0.1,
            backgroundColor: done ? "#16a34a" : "#ddd",
          }}
          transition={{ duration: 0.4 }}
          style={{ originX: 0 }}
        />

        {/* RESOLVED pill */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: done ? 1 : 0.25, scale: 1 }}
          transition={{ duration: 0.4 }}
          className={clsx(
            "shrink-0 px-4 py-2 text-[13px] font-semibold tracking-wide rounded transition-colors duration-500",
            done
              ? "bg-green-600 text-white"
              : "bg-subtle text-muted border border-hairline",
          )}
        >
          RESOLVED
        </motion.div>
      </div>

      {/* ── Filter indicator ─────────────────────────────────── */}
      {selectedStore && (
        <div className="flex items-center gap-2 text-[12px]">
          <span className="text-muted">Showing steps for</span>
          <span className="font-semibold text-ink">
            {STORES.find((s) => s.id === selectedStore)?.label}
          </span>
          <button
            onClick={() => setSelectedStore(null)}
            className="text-accent hover:underline ml-1"
          >
            Show all
          </button>
        </div>
      )}

      {/* ── Incremental trace log ────────────────────────────── */}
      <div className="relative max-h-[360px] overflow-y-auto">
        {/* Vertical timeline line */}
        {visibleSteps.length > 0 && (
          <div className="absolute left-[15px] top-4 bottom-4 w-px bg-hairline" />
        )}

        <div className="space-y-0">
          {visibleSteps.map(({ step, idx }) => {
            const storeNode = stepToStoreNode[idx];
            const isLatest = idx === revealedCount - 1 && !done;

            return (
              <motion.div
                key={`step-${idx}`}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className={clsx(
                  "relative flex items-start gap-4 py-3 pl-0 pr-2",
                  isLatest && "bg-accent/[0.03]",
                )}
              >
                {/* Timeline dot */}
                <div className="relative z-10 shrink-0 w-[30px] flex justify-center pt-1">
                  <div
                    className={clsx(
                      "w-3 h-3 rounded-full border-2 border-white",
                      storeNode?.dotColor ?? "bg-slate-400",
                      isLatest && "ring-3 ring-accent/20",
                    )}
                  />
                </div>

                {/* Step content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-muted tabular-nums">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    <span className="text-[13px] font-semibold text-ink">
                      {step.label}
                    </span>
                    {storeNode && (
                      <span className="text-[10px] text-muted px-1.5 py-0.5 bg-subtle rounded">
                        {storeNode.label}
                      </span>
                    )}
                  </div>
                  {step.description && (
                    <p className="text-[12px] text-muted leading-relaxed mt-1 pr-4">
                      {step.description}
                    </p>
                  )}
                  {/* IO details — show selected output if available */}
                  {step.io?.selected && (
                    <div className="flex items-start gap-1.5 mt-1.5">
                      <ChevronRight size={12} className="text-accent mt-[1px] shrink-0" />
                      <span className="text-[12px] font-mono text-accent break-words">
                        {step.io.selected}
                      </span>
                    </div>
                  )}
                </div>

                {/* Duration */}
                <div className="text-[11px] font-mono text-muted tabular-nums shrink-0 pt-0.5">
                  {step.duration_ms}ms
                </div>
              </motion.div>
            );
          })}

          {/* Completion marker */}
          {done && !selectedStore && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="relative flex items-center gap-4 py-3 pl-0"
            >
              <div className="relative z-10 shrink-0 w-[30px] flex justify-center">
                <div className="w-3 h-3 rounded-full bg-green-500 border-2 border-white" />
              </div>
              <div className="text-[13px] text-green-700 font-medium">
                Complete — {steps.length} steps, {usedStores.length} stores,{" "}
                <span className="font-mono">
                  {Math.round(steps.reduce((a, s) => a + s.duration_ms, 0))}ms
                </span>
              </div>
            </motion.div>
          )}

          <div ref={traceEndRef} />
        </div>
      </div>
    </div>
  );
}
