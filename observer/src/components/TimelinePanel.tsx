import type { CSSProperties } from "react";
import {
  STAGE_LABELS,
  TIMELINE_STAGES,
  type TelemetryEvent,
  type TelemetryStage,
  type TelemetryStatus,
} from "../types/events";

export interface TimelinePanelProps {
  resolutionId: string | null;
  events: TelemetryEvent[];
}

interface StageState {
  status: TelemetryStatus | "pending";
  latencyMs: number | null;
}

function deriveStageStates(
  events: TelemetryEvent[],
): Record<TelemetryStage, StageState> {
  const states: Partial<Record<TelemetryStage, StageState>> = {};
  for (const ev of events) {
    if (!TIMELINE_STAGES.includes(ev.stage)) continue;
    const prev = states[ev.stage];
    if (prev && ev.status === "started") continue;
    states[ev.stage] = {
      status: ev.status,
      latencyMs: ev.latency_ms || prev?.latencyMs || null,
    };
  }
  const full: Record<TelemetryStage, StageState> = {} as Record<
    TelemetryStage,
    StageState
  >;
  for (const stage of TIMELINE_STAGES) {
    full[stage] = states[stage] ?? { status: "pending", latencyMs: null };
  }
  return full;
}

const STATUS_COLOR: Record<StageState["status"], string> = {
  pending: "#2a2f3a",
  started: "#d4a017",
  ok: "#2f9e44",
  warning: "#e67700",
  error: "#c92a2a",
  timeout: "#c92a2a",
  denied: "#862e9c",
};

const boxStyle = (state: StageState): CSSProperties => ({
  background: STATUS_COLOR[state.status],
  color: "#fff",
  padding: "10px 14px",
  borderRadius: 6,
  minWidth: 110,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: 4,
  boxShadow:
    state.status === "started"
      ? "0 0 0 2px rgba(255, 224, 102, 0.5)"
      : "none",
  transition: "background 120ms ease-in-out, box-shadow 120ms ease-in-out",
});

const connectorStyle: CSSProperties = {
  height: 2,
  background: "#3a3f4b",
  flex: 1,
  alignSelf: "center",
};

export function TimelinePanel({ resolutionId, events }: TimelinePanelProps) {
  const states = deriveStageStates(events);
  return (
    <section
      aria-label="Resolution timeline"
      style={{
        padding: 16,
        background: "#1a1d24",
        borderRadius: 8,
        border: "1px solid #2a2f3a",
      }}
    >
      <header
        style={{
          marginBottom: 12,
          display: "flex",
          alignItems: "baseline",
          gap: 12,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 14,
            color: "#cbd3dc",
            fontWeight: 600,
          }}
        >
          Pipeline
        </h2>
        <code style={{ color: "#6e7686", fontSize: 12 }}>
          {resolutionId ?? "waiting for resolution\u2026"}
        </code>
      </header>
      <div style={{ display: "flex", alignItems: "stretch", gap: 8 }}>
        {TIMELINE_STAGES.map((stage, idx) => (
          <div
            key={stage}
            style={{ display: "flex", flex: 1, alignItems: "stretch" }}
          >
            <div style={boxStyle(states[stage])} data-testid={`stage-${stage}`}>
              <span style={{ fontSize: 12, fontWeight: 600 }}>
                {STAGE_LABELS[stage]}
              </span>
              <span style={{ fontSize: 11, opacity: 0.9 }}>
                {states[stage].status === "pending"
                  ? "\u2014"
                  : states[stage].latencyMs != null
                    ? `${states[stage].latencyMs!.toFixed(1)} ms`
                    : states[stage].status}
              </span>
            </div>
            {idx < TIMELINE_STAGES.length - 1 && (
              <div style={connectorStyle} />
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
