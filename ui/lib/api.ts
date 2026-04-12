/**
 * API client. Tries the live ECP backend first; falls back to the mock
 * resolver when unreachable. This means the UI is always demo-able —
 * VC call, flaky wifi, cold backend, fresh clone all work.
 */

import { mockResolve, type ResolveArgs } from "./mockResolver";
import type { ResolveResponse } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_ECP_API_BASE || "http://localhost:8080";

export type HealthResponse = {
  status: string;
  mode?: string;
  demo_mode?: boolean;
  version?: string;
  embedding_available?: boolean;
};

async function fetchJson<T>(
  path: string,
  init?: RequestInit,
  timeoutMs = 1500,
): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: ctrl.signal,
      headers: {
        "content-type": "application/json",
        ...(init?.headers || {}),
      },
    });
    if (!res.ok) {
      throw new Error(`${res.status} ${res.statusText}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

// ─── Health (quick + cheap) ──────────────────────────────────────────

export const api = {
  health: () => fetchJson<HealthResponse>("/health"),
};

// ─── Resolve with live/mock fallback ─────────────────────────────────

// ─── Live vs mock strategy ──────────────────────────────────────────
//
// NEXT_PUBLIC_ECP_USE_LIVE controls whether the UI attempts the live
// backend at all. Three modes:
//   "1"    — try live, fall back to mock on failure
//   "only" — live only, no fallback (error surfaces to user)
//   unset  — mock only (default for offline demos)
const USE_LIVE = process.env.NEXT_PUBLIC_ECP_USE_LIVE;

export async function resolve(args: ResolveArgs): Promise<ResolveResponse> {
  if (!USE_LIVE) return mockResolve(args);
  try {
    const body = JSON.stringify({
      concept: args.question,
      user_context: {
        user_id: args.persona.id,
        department: args.persona.department,
        role: args.persona.role.toLowerCase(),
      },
    });
    const headers: Record<string, string> = {
      "x-ecp-user-id": args.persona.id,
      "x-ecp-department": args.persona.department,
      "x-ecp-role": args.persona.role.toLowerCase(),
    };
    const live = await fetchJson<Record<string, unknown>>(
      "/api/v1/resolve",
      { method: "POST", body, headers },
      5000,
    );
    return adaptBackendResponse(live, args);
  } catch {
    if (USE_LIVE === "only") throw new Error("Live API unreachable");
    return mockResolve(args);
  }
}

// ─── Backend → Studio shape adapter ─────────────────────────────────
//
// The live ECP backend (FastAPI / models.py) uses a different field
// naming convention than the Studio UI (types.ts). This adapter maps
// between them so the same components render both mock and live data.
//
// Backend shape differences:
//   DAG steps:         step/method/reasoning/latency_ms  →  id/action/label/description/duration_ms/io
//   ResolvedConcept:   resolved_id/resolved_name/definition  →  concept_id/canonical_name/plain_english
//   TribalWarning:     description/impact/severity(high/medium/low)  →  headline/detail/severity(critical/warn/info)
//   Top-level:         no headline, no latency_ms  →  headline, latency_ms

const SEVERITY_MAP: Record<string, "info" | "warn" | "critical"> = {
  high: "critical",
  critical: "critical",
  medium: "warn",
  warn: "warn",
  low: "info",
  info: "info",
};

function adaptDAG(
  raw: unknown[],
): ResolveResponse["resolution_dag"] {
  if (!Array.isArray(raw)) return [];
  return raw.map((rawStep: unknown, i) => {
    const s = rawStep as Record<string, unknown>;
    return {
    id: `s${i + 1}`,
    action: (s.step as string) || "unknown",
    label: formatStepLabel(s.step as string),
    description: (s.reasoning as string) || "",
    duration_ms: (s.latency_ms as number) || 0,
    io: {
      source: (s.method as string) || "engine",
      query: JSON.stringify((s.input as Record<string, unknown>) || {}),
      selected: (() => {
        const out = s.output as Record<string, unknown> | undefined;
        if (!out) return undefined;
        return (out.resolved as string) || (out.label as string) || undefined;
      })(),
      output: (() => {
        const out = s.output as Record<string, unknown> | undefined;
        if (!out) return undefined;
        const entries: Record<string, string> = {};
        for (const [k, v] of Object.entries(out)) {
          entries[k] = typeof v === "object" ? JSON.stringify(v) : String(v);
        }
        return entries;
      })(),
    },
  };
  });
}

function formatStepLabel(step: string): string {
  if (!step) return "Unknown step";
  // "parse_intent" → "Parse intent", "resolve_metric" → "Resolve metric"
  return step.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

function adaptConcepts(
  raw: unknown,
): ResolveResponse["resolved_concepts"] {
  if (!raw || typeof raw !== "object") return {};
  const out: ResolveResponse["resolved_concepts"] = {};
  for (const [key, val] of Object.entries(raw as Record<string, Record<string, unknown>>)) {
    out[key] = {
      concept_id: (val.resolved_id as string) || key,
      canonical_name: (val.resolved_name as string) || key,
      plain_english: (val.definition as string) || "",
      department_variation: (val.concept_type as string) || undefined,
      source: `ECP Knowledge Graph · confidence ${((val.confidence as number) || 0).toFixed(2)}`,
    };
  }
  return out;
}

function adaptWarnings(raw: unknown): ResolveResponse["warnings"] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((w): w is Record<string, unknown> => !!w && typeof w === "object")
    .map((w, i) => {
      const sev = String(w.severity ?? "info").toLowerCase();
      return {
        id: (w.id as string) || `w_${i}`,
        severity: SEVERITY_MAP[sev] ?? "info",
        headline:
          (w.headline as string) ||
          (w.description as string) ||
          "Warning",
        detail:
          (w.detail as string) ||
          (w.impact as string) ||
          "",
        author: (w.author as string) || undefined,
        captured_at: (w.captured_at as string) || undefined,
      };
    });
}

function adaptPrecedents(raw: unknown): ResolveResponse["precedents_used"] {
  if (!Array.isArray(raw)) return [];
  return raw.map((p: Record<string, unknown>) => ({
    resolution_id: (p.query_id as string) || (p.resolution_id as string) || "",
    query: (p.original_query as string) || (p.query as string) || "",
    similarity: (p.similarity as number) || 0,
    feedback: ((p.feedback as string) || "none") as "accepted" | "rejected" | "corrected" | "none",
    user: (p.user as string) || "",
  }));
}

function buildHeadline(
  concepts: ResolveResponse["resolved_concepts"],
  args: ResolveArgs,
): string {
  const parts: string[] = [];
  if (concepts.metric) parts.push(concepts.metric.canonical_name);
  if (concepts.scope) parts.push(concepts.scope.canonical_name);
  if (concepts.dimension) parts.push(concepts.dimension.canonical_name);
  if (concepts.time) parts.push(concepts.time.canonical_name);
  if (concepts.adjustment) parts.push(`· ${concepts.adjustment.canonical_name}`);
  if (parts.length === 0) return `Resolved for ${args.persona.name}`;
  return `${parts.join(", ")} — resolved for ${args.persona.department}`;
}

function adaptBackendResponse(
  live: Record<string, unknown>,
  args: ResolveArgs,
): ResolveResponse {
  const dag = adaptDAG((live.resolution_dag as unknown[]) || []);
  const concepts = adaptConcepts(live.resolved_concepts);
  const warnings = adaptWarnings(live.warnings);
  const precedents = adaptPrecedents(live.precedents_used);
  const latency = dag.reduce((a, s) => a + (s.duration_ms || 0), 0) || 300;

  const statusRaw = (live.status as string) || "resolved";
  const status: ResolveResponse["status"] =
    statusRaw === "complete" ? "resolved" : (statusRaw as ResolveResponse["status"]);

  return {
    resolution_id:
      (live.resolution_id as string) || `live_${Date.now().toString(36)}`,
    status,
    resolved_concepts: concepts,
    execution_plan: (live.execution_plan as ResolveResponse["execution_plan"]) || [],
    confidence: (live.confidence as ResolveResponse["confidence"]) || {
      definition: 0.8,
      data_quality: 0.8,
      temporal_validity: 0.8,
      authorization: 1.0,
      completeness: 0.8,
      overall: 0.8,
    },
    warnings,
    precedents_used: precedents,
    resolution_dag: dag,
    policies_evaluated: (live.policies_evaluated as string[]) || [],
    access_granted: (live.access_granted as boolean) ?? true,
    filtered_concepts: (live.filtered_concepts as string[]) || [],
    headline: buildHeadline(concepts, args),
    latency_ms: latency,
  };
}
