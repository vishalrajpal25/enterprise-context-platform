"use client";

/**
 * Cross-platform source lineage visualization.
 *
 * Shows where the data comes from across platforms (Snowflake, Oracle, etc.)
 * with animated flow lines connecting source tables → columns → metric.
 *
 * Renders when the execution plan contains `sources` metadata.
 */

import { motion } from "framer-motion";
import clsx from "clsx";
import {
  Database,
  ArrowRight,
  Snowflake,
  Server,
  Cloud,
  HardDrive,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { ExecutionStep } from "@/lib/types";

type Source = {
  table_name: string;
  platform: string;
  column_name: string;
  table_id?: string;
};

const PLATFORM_ICON: Record<string, LucideIcon> = {
  snowflake: Snowflake,
  oracle: HardDrive,
  bigquery: Cloud,
  redshift: Server,
  databricks: Database,
};

const PLATFORM_COLOR: Record<string, string> = {
  snowflake: "text-sky-500 border-sky-200 bg-sky-50",
  oracle: "text-red-500 border-red-200 bg-red-50",
  bigquery: "text-blue-500 border-blue-200 bg-blue-50",
  redshift: "text-orange-500 border-orange-200 bg-orange-50",
  databricks: "text-emerald-500 border-emerald-200 bg-emerald-50",
};

export function SourceLineage({
  plan,
}: {
  plan: ExecutionStep[];
}) {
  // Collect all sources from all steps
  const allSources: Source[] = [];
  const measures: string[] = [];
  let target = "";
  let scope: { type: string; name: string } | undefined;
  let adjustment: { type: string; name: string; definition?: string } | undefined;

  for (const step of plan) {
    const params = step.parameters as Record<string, unknown> | undefined;
    if (params?.sources) {
      allSources.push(...(params.sources as Source[]));
    }
    if (params?.measures) {
      measures.push(...(params.measures as string[]));
    }
    if (step.target) target = step.target;
    if (params?.scope) scope = params.scope as { type: string; name: string };
    if (params?.adjustment) adjustment = params.adjustment as { type: string; name: string; definition?: string };
  }

  if (allSources.length === 0 && measures.length === 0) return null;

  // Group sources by platform
  const byPlatform: Record<string, Source[]> = {};
  for (const src of allSources) {
    const p = src.platform || "unknown";
    if (!byPlatform[p]) byPlatform[p] = [];
    byPlatform[p].push(src);
  }

  const platforms = Object.keys(byPlatform);
  const isCrossPlatform = platforms.length > 1;

  return (
    <div className="space-y-4">
      {/* Cross-platform badge */}
      {isCrossPlatform && (
        <motion.div
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          className="inline-flex items-center gap-2 px-3 py-1.5 border border-accent/30 bg-accent/5 text-accent text-label font-semibold"
        >
          <Database size={14} />
          Cross-platform query: {platforms.join(" + ")}
        </motion.div>
      )}

      {/* Source flow */}
      <div className="flex items-stretch gap-0 overflow-x-auto">
        {/* Left: source platforms */}
        <div className="flex flex-col gap-3 shrink-0">
          {platforms.map((platform, pi) => {
            const sources = byPlatform[platform];
            const Icon = PLATFORM_ICON[platform.toLowerCase()] || Database;
            const colors =
              PLATFORM_COLOR[platform.toLowerCase()] ||
              "text-slate-500 border-slate-200 bg-slate-50";

            return (
              <motion.div
                key={platform}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: pi * 0.15, duration: 0.4 }}
                className={clsx(
                  "border px-4 py-3 min-w-[200px]",
                  colors,
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon size={16} />
                  <span className="text-body font-semibold capitalize">
                    {platform}
                  </span>
                </div>
                {sources.map((src, si) => (
                  <div
                    key={si}
                    className="text-label font-mono text-ink/80 pl-6 py-0.5"
                  >
                    {src.table_name}
                    <span className="text-muted">.{src.column_name}</span>
                  </div>
                ))}
              </motion.div>
            );
          })}
        </div>

        {/* Arrow */}
        <div className="flex items-center px-4 shrink-0">
          <motion.div
            initial={{ opacity: 0, scaleX: 0 }}
            animate={{ opacity: 1, scaleX: 1 }}
            transition={{ delay: 0.3, duration: 0.4 }}
            className="flex items-center gap-1"
          >
            <div className="w-12 h-px bg-accent" />
            <ArrowRight size={16} className="text-accent" />
          </motion.div>
        </div>

        {/* Right: semantic layer target */}
        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5, duration: 0.4 }}
          className="border border-accent bg-accent/5 px-4 py-3 min-w-[220px] shrink-0"
        >
          <div className="flex items-center gap-2 mb-2">
            <Database size={16} className="text-accent" />
            <span className="text-body font-semibold text-accent">
              Semantic Layer
            </span>
          </div>
          {target && (
            <div className="text-label font-mono text-ink/80 pl-6 py-0.5">
              {target}
            </div>
          )}
          {measures.map((m, i) => (
            <div
              key={i}
              className="text-label font-mono text-ink/80 pl-6 py-0.5"
            >
              {m}
            </div>
          ))}
          {scope && (
            <div className="mt-2 pt-2 border-t border-accent/20">
              <span className="text-label text-muted">scope: </span>
              <span className="text-label font-mono text-ink">
                {scope.name}
              </span>
            </div>
          )}
          {adjustment && (
            <div className="mt-1">
              <span className="text-label text-muted">adjustment: </span>
              <span className="text-label font-mono text-ink">
                {adjustment.name}
              </span>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
