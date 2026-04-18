// Hand-mirrored from src/telemetry/events.py.
// The Python pydantic model is the source of truth.

export type TelemetryStage =
  | "parse_intent"
  | "resolve_concept"
  | "tribal_check"
  | "authz"
  | "precedent"
  | "build_plan"
  | "persist_trace"
  | "adapter_call"
  | "store_call"
  | "federation_discover"
  | "federation_merge"
  | "resolution_start"
  | "resolution_end";

export type TelemetryStore =
  | "neo4j"
  | "pgvector"
  | "postgres"
  | "opa"
  | "cube"
  | "anthropic"
  | "voyage"
  | "openai"
  | "trace_store";

export type TelemetryStatus =
  | "started"
  | "ok"
  | "warning"
  | "error"
  | "timeout"
  | "denied";

export interface TelemetryEvent {
  resolution_id: string;
  stage: TelemetryStage;
  status: TelemetryStatus;
  store?: TelemetryStore | null;
  latency_ms: number;
  payload_summary: Record<string, unknown>;
  ts: string;
  parent_stage?: TelemetryStage | null;
  source_id?: string | null;
}

export const TIMELINE_STAGES: TelemetryStage[] = [
  "parse_intent",
  "resolve_concept",
  "tribal_check",
  "precedent",
  "authz",
  "build_plan",
  "persist_trace",
];

export interface ConceptPayload {
  concept_type: string;
  resolved_id: string;
  confidence: number;
  resolved_name?: string;
  definition?: string;
  reasoning?: string;
}

export interface TribalWarningPayload {
  id: string;
  description: string;
  severity: string;
  impact: string;
  workaround: string;
}

export interface ConfidenceBreakdown {
  definition: number;
  data_quality: number;
  temporal_validity: number;
  authorization: number;
  completeness: number;
  overall: number;
}

export const STAGE_LABELS: Record<TelemetryStage, string> = {
  parse_intent: "Parse Intent",
  resolve_concept: "Resolve Concepts",
  tribal_check: "Tribal Check",
  precedent: "Precedent",
  authz: "Authorize",
  build_plan: "Build Plan",
  persist_trace: "Persist Trace",
  adapter_call: "Adapter Call",
  store_call: "Store Call",
  federation_discover: "Fed. Discover",
  federation_merge: "Fed. Merge",
  resolution_start: "Start",
  resolution_end: "End",
};
