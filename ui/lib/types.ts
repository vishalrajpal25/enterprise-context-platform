/**
 * Shapes that mirror the ECP API (src/models.py) closely enough that the
 * UI can be pointed at either the mock resolver or the real FastAPI
 * backend without changes.
 *
 * Field names match the Python Pydantic models (snake_case) so JSON from
 * the real API drops straight in.
 */

export type Confidence = {
  definition: number;
  data_quality: number;
  temporal_validity: number;
  authorization: number;
  completeness: number;
  overall: number;
};

export type ResolvedConcept = {
  concept_id: string;
  canonical_name: string;
  plain_english: string;
  department_variation?: string;
  fiscal_resolution?: string;
  source: string;
};

export type ExecutionStep = {
  step: number;
  action: string;
  target: string;
  parameters?: Record<string, unknown>;
};

export type TribalWarning = {
  id: string;
  severity: "info" | "warn" | "critical";
  headline: string;
  detail: string;
  author?: string;
  captured_at?: string;
};

export type Precedent = {
  resolution_id: string;
  query: string;
  similarity: number;
  feedback: "accepted" | "rejected" | "corrected" | "none";
  user: string;
};

export type TraceIO = {
  /** What store/system this step hit. "Knowledge Graph", "Policy Engine", etc. */
  source: string;
  /** The lookup/query made against that source. */
  query?: string;
  /** What the source returned — list of candidate strings. */
  found?: string[];
  /** What was ultimately selected/produced. */
  selected?: string;
  /** Optional small structured outputs, shown as key/value lines. */
  output?: Record<string, string>;
};

export type ResolutionDAGStep = {
  id: string;
  action: string;
  label: string;
  description: string;
  duration_ms: number;
  io?: TraceIO;
};

export type ResolveResponse = {
  resolution_id: string;
  status: "resolved" | "disambiguation_required" | "failed";
  resolved_concepts: Record<string, ResolvedConcept>;
  execution_plan: ExecutionStep[];
  confidence: Confidence;
  warnings: TribalWarning[];
  precedents_used: Precedent[];
  resolution_dag: ResolutionDAGStep[];
  policies_evaluated: string[];
  access_granted: boolean;
  filtered_concepts: string[];
  headline: string;
  latency_ms: number;
};

export type Persona = {
  id: string;
  name: string;
  role: string;
  department: string;
  avatar_initials: string;
};

export type Scenario = {
  id: string;
  world_id: string;
  title: string;
  question: string;
  watch_for: string;
};

export type World = {
  id: string;
  industry_id: string;
  name: string;
  kind: string;
  tagline: string;
  personas: Persona[];
  scenarios: Scenario[];
};

export type Industry = {
  id: string;
  name: string; // "Finance", "Healthcare", "Technology"
  tagline: string;
  worlds: World[];
};
