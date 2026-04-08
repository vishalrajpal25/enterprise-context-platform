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

export async function resolve(args: ResolveArgs): Promise<ResolveResponse> {
  // The real API expects a single `concept` string + headers; we try it
  // first. If anything goes wrong — network, CORS, 4xx, timeout — we
  // silently fall through to the mock so the demo never breaks.
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
    const live = await fetchJson<ResolveResponse>(
      "/api/v1/resolve",
      { method: "POST", body, headers },
      2000,
    );
    // The live API's shape is close but not identical to the mock's.
    // Normalize a few fields so the UI renders either cleanly.
    return normalizeLive(live, args);
  } catch {
    return mockResolve(args);
  }
}

function normalizeLive(
  live: Partial<ResolveResponse> & Record<string, unknown>,
  args: ResolveArgs,
): ResolveResponse {
  const dag = (live.resolution_dag || []) as ResolveResponse["resolution_dag"];
  const latency =
    typeof live.latency_ms === "number"
      ? live.latency_ms
      : dag.reduce((a, s) => a + (s.duration_ms || 0), 0) || 300;
  return {
    resolution_id:
      (live.resolution_id as string) || `live_${Date.now().toString(36)}`,
    status: (live.status as ResolveResponse["status"]) || "resolved",
    resolved_concepts:
      (live.resolved_concepts as ResolveResponse["resolved_concepts"]) || {},
    execution_plan:
      (live.execution_plan as ResolveResponse["execution_plan"]) || [],
    confidence: (live.confidence as ResolveResponse["confidence"]) || {
      definition: 0.8,
      data_quality: 0.8,
      temporal_validity: 0.8,
      authorization: 1.0,
      completeness: 0.8,
      overall: 0.8,
    },
    warnings: (live.warnings as ResolveResponse["warnings"]) || [],
    precedents_used:
      (live.precedents_used as ResolveResponse["precedents_used"]) || [],
    resolution_dag: dag,
    policies_evaluated:
      (live.policies_evaluated as string[]) || [],
    access_granted: (live.access_granted as boolean) ?? true,
    filtered_concepts: (live.filtered_concepts as string[]) || [],
    headline:
      (live.headline as string) ||
      `Resolved "${args.question}" for ${args.persona.name}`,
    latency_ms: latency,
  };
}
