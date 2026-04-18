import type { CSSProperties } from "react";
import type { TelemetryEvent, TelemetryStatus } from "../types/events";

interface ResolutionFlowProps {
  events: TelemetryEvent[];
  selectedStage: string | null;
  onSelectStage: (stage: string) => void;
}

const STATUS_DOT_COLOR: Record<string, string> = {
  ok: "#4ade80",
  started: "#facc15",
  warning: "#fb923c",
  error: "#f87171",
  denied: "#a78bfa",
  timeout: "#f87171",
  pending: "#404040",
};

interface StageCard {
  stage: string;
  label: string;
  status: TelemetryStatus | "pending";
  latencyMs: number | null;
  summary: string;
  events: TelemetryEvent[];
}

function extractSummary(stage: string, evts: TelemetryEvent[]): string {
  if (evts.length === 0) return "";
  const ps = evts[evts.length - 1].payload_summary;

  switch (stage) {
    case "resolution_start": {
      const concept = (ps.concept as string) ?? (ps.query as string) ?? "";
      const dept = (ps.department as string) ?? "";
      return concept + (dept ? ` (${dept})` : "");
    }
    case "parse_intent": {
      const concepts = ps.concepts as Record<string, unknown> | undefined;
      if (concepts) {
        const keys = Object.keys(concepts);
        return `${keys.length} concept(s): ${keys.join(", ")}`;
      }
      return "Parsed";
    }
    case "resolve_concept": {
      return evts
        .filter((e) => e.status !== "started")
        .map((e) => {
          const ct =
            (e.payload_summary.concept_type as string) ?? "concept";
          const conf = e.payload_summary.confidence as number | undefined;
          return `${ct}${conf != null ? ` (${(conf * 100).toFixed(0)}%)` : ""}`;
        })
        .join(", ");
    }
    case "tribal_check": {
      const count =
        (ps.warning_count as number) ??
        (ps.warnings as unknown[] | undefined)?.length ??
        0;
      return count > 0 ? `${count} warning(s)` : "No warnings";
    }
    case "precedent": {
      const count = (ps.count as number) ?? (ps.precedent_count as number) ?? 0;
      const mix = ps.feedback_mix as Record<string, number> | undefined;
      const mixStr = mix
        ? Object.entries(mix)
            .map(([k, v]) => `${k}: ${v}`)
            .join(", ")
        : "";
      return `${count} precedent(s)${mixStr ? ` (${mixStr})` : ""}`;
    }
    case "authz": {
      const allowed = ps.allowed as boolean | undefined;
      return allowed === false ? "DENIED" : "Allowed";
    }
    case "build_plan": {
      const targets = ps.targets as string[] | undefined;
      const count =
        (ps.target_count as number) ?? targets?.length ?? 0;
      const first = targets?.[0] ?? "";
      return `${count} target(s)${first ? `: ${first}` : ""}`;
    }
    case "persist_trace":
      return "Trace saved";
    case "resolution_end": {
      const conf = ps.overall_confidence as number | undefined;
      const lat = ps.total_latency_ms as number | undefined;
      const parts: string[] = [];
      if (conf != null) parts.push(`confidence: ${(conf * 100).toFixed(0)}%`);
      if (lat != null) parts.push(`${lat.toFixed(0)}ms total`);
      return parts.join(" | ") || "Complete";
    }
    default:
      return "";
  }
}

const STAGE_ORDER = [
  "resolution_start",
  "parse_intent",
  "resolve_concept",
  "tribal_check",
  "precedent",
  "authz",
  "build_plan",
  "persist_trace",
  "resolution_end",
];

const STAGE_DISPLAY: Record<string, string> = {
  resolution_start: "Query",
  parse_intent: "Parse Intent",
  resolve_concept: "Resolve Concepts",
  tribal_check: "Tribal Check",
  precedent: "Precedent Search",
  authz: "Authorization",
  build_plan: "Build Plan",
  persist_trace: "Persist Trace",
  resolution_end: "Result",
};

function buildCards(events: TelemetryEvent[]): StageCard[] {
  const grouped: Record<string, TelemetryEvent[]> = {};
  for (const ev of events) {
    const stage = ev.stage;
    if (!STAGE_ORDER.includes(stage)) continue;
    if (!grouped[stage]) grouped[stage] = [];
    grouped[stage].push(ev);
  }

  return STAGE_ORDER.map((stage) => {
    const evts = grouped[stage] ?? [];
    let status: TelemetryStatus | "pending" = "pending";
    let latencyMs: number | null = null;

    for (const e of evts) {
      if (e.status !== "started") {
        status = e.status;
        latencyMs = e.latency_ms ?? latencyMs;
      } else if (status === "pending") {
        status = "started";
      }
      if (e.latency_ms && e.latency_ms > (latencyMs ?? 0)) {
        latencyMs = e.latency_ms;
      }
    }

    return {
      stage,
      label: STAGE_DISPLAY[stage] ?? stage,
      status,
      latencyMs,
      summary: extractSummary(stage, evts),
      events: evts,
    };
  });
}

export function ResolutionFlow({
  events,
  selectedStage,
  onSelectStage,
}: ResolutionFlowProps) {
  const cards = buildCards(events);

  const containerStyle: CSSProperties = {
    display: "flex",
    flexDirection: "column",
    position: "relative",
    paddingLeft: 20,
    overflowY: "auto",
    height: "100%",
  };

  const lineStyle: CSSProperties = {
    position: "absolute",
    left: 9,
    top: 0,
    bottom: 0,
    width: 2,
    background: "#333",
  };

  return (
    <div style={containerStyle}>
      <div style={lineStyle} />
      {cards.map((card) => {
        const isSelected = selectedStage === card.stage;
        const dotColor = STATUS_DOT_COLOR[card.status] ?? "#404040";

        const cardStyle: CSSProperties = {
          background: isSelected ? "#262626" : "#1a1a1a",
          border: isSelected ? "1px solid #555" : "1px solid #333",
          borderRadius: 8,
          padding: "10px 14px",
          marginBottom: 6,
          cursor: "pointer",
          position: "relative",
          transition: "background 120ms, border 120ms",
        };

        const dotStyle: CSSProperties = {
          position: "absolute",
          left: -16,
          top: 16,
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: dotColor,
          border: "2px solid #0f0f0f",
        };

        return (
          <div
            key={card.stage}
            style={cardStyle}
            onClick={() => onSelectStage(card.stage)}
          >
            <div style={dotStyle} />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 2,
              }}
            >
              <span style={{ fontWeight: 600, fontSize: 13, color: "#e5e5e5" }}>
                {card.label}
              </span>
              <span style={{ fontSize: 11, color: "#6b7280" }}>
                {card.latencyMs != null
                  ? `${card.latencyMs.toFixed(1)}ms`
                  : card.status === "pending"
                    ? ""
                    : card.status}
              </span>
            </div>
            {card.summary && (
              <p
                style={{
                  margin: 0,
                  fontSize: 12,
                  color: "#a3a3a3",
                  lineHeight: 1.4,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {card.summary}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
