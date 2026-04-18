import type { CSSProperties } from "react";
import type {
  TelemetryEvent,
  ConfidenceBreakdown,
  TribalWarningPayload,
} from "../types/events";
import { ConfidenceBars } from "./ConfidenceBars";
import { TribalWarnings } from "./TribalWarnings";

interface DetailPanelProps {
  selectedStage: string | null;
  events: TelemetryEvent[];
}

function stageEvents(events: TelemetryEvent[], stage: string): TelemetryEvent[] {
  return events.filter((e) => e.stage === stage);
}

const sectionTitle: CSSProperties = {
  fontSize: 14,
  fontWeight: 600,
  color: "#e5e5e5",
  marginBottom: 10,
  marginTop: 0,
};

const kvRow: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  padding: "4px 0",
  fontSize: 13,
  borderBottom: "1px solid #262626",
};

const kvLabel: CSSProperties = { color: "#a3a3a3" };
const kvValue: CSSProperties = { color: "#e5e5e5", textAlign: "right" };

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div style={kvRow}>
      <span style={kvLabel}>{label}</span>
      <span style={kvValue}>{value}</span>
    </div>
  );
}

function RenderStart({ evts }: { evts: TelemetryEvent[] }) {
  if (evts.length === 0) return null;
  const ps = evts[evts.length - 1].payload_summary;
  return (
    <div>
      <h3 style={sectionTitle}>Query Details</h3>
      <KV label="Concept" value={String(ps.concept ?? ps.query ?? "")} />
      <KV label="User" value={String(ps.user_id ?? "")} />
      <KV label="Department" value={String(ps.department ?? "")} />
      <KV label="Mode" value={String(ps.mode ?? ps.resolution_mode ?? "")} />
    </div>
  );
}

function RenderParseIntent({ evts }: { evts: TelemetryEvent[] }) {
  if (evts.length === 0) return null;
  const ps = evts[evts.length - 1].payload_summary;
  const concepts = ps.concepts as Record<string, unknown> | undefined;
  return (
    <div>
      <h3 style={sectionTitle}>Parsed Concepts</h3>
      {concepts ? (
        <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", color: "#a3a3a3", padding: "4px 0" }}>
                Type
              </th>
              <th style={{ textAlign: "left", color: "#a3a3a3", padding: "4px 0" }}>
                Value
              </th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(concepts).map(([k, v]) => (
              <tr key={k} style={{ borderBottom: "1px solid #262626" }}>
                <td style={{ padding: "4px 0", color: "#e5e5e5" }}>{k}</td>
                <td style={{ padding: "4px 0", color: "#a3a3a3" }}>
                  {String(v)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p style={{ color: "#6b7280", fontSize: 13 }}>No concepts extracted</p>
      )}
    </div>
  );
}

function RenderResolveConcept({ evts }: { evts: TelemetryEvent[] }) {
  const resolved = evts.filter((e) => e.status !== "started");
  if (resolved.length === 0) return null;
  return (
    <div>
      <h3 style={sectionTitle}>Resolved Concepts</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {resolved.map((e, i) => {
          const ps = e.payload_summary;
          const conf = (ps.confidence as number) ?? 0;
          const barColor =
            conf > 0.8 ? "#4ade80" : conf >= 0.5 ? "#facc15" : "#f87171";
          return (
            <div
              key={i}
              style={{
                background: "#1a1a1a",
                border: "1px solid #333",
                borderRadius: 8,
                padding: 12,
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 6,
                }}
              >
                <span style={{ fontWeight: 600, fontSize: 13, color: "#e5e5e5" }}>
                  {String(ps.resolved_name ?? ps.concept_type ?? "Concept")}
                </span>
                <span style={{ color: barColor, fontSize: 12, fontWeight: 600 }}>
                  {(conf * 100).toFixed(0)}%
                </span>
              </div>
              {ps.definition != null && (
                <p style={{ margin: "0 0 4px", fontSize: 12, color: "#a3a3a3" }}>
                  {String(ps.definition)}
                </p>
              )}
              {ps.reasoning != null && (
                <p
                  style={{
                    margin: "0 0 6px",
                    fontSize: 12,
                    color: "#737373",
                    fontStyle: "italic",
                  }}
                >
                  {String(ps.reasoning)}
                </p>
              )}
              <div
                style={{
                  height: 6,
                  background: "#262626",
                  borderRadius: 3,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${conf * 100}%`,
                    height: "100%",
                    background: barColor,
                    borderRadius: 3,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RenderTribalCheck({ evts }: { evts: TelemetryEvent[] }) {
  if (evts.length === 0) return null;
  const ps = evts[evts.length - 1].payload_summary;
  const warnings = (ps.warnings ?? ps.enriched_warnings ?? []) as TribalWarningPayload[];
  return (
    <div>
      <h3 style={sectionTitle}>Tribal Warnings</h3>
      <TribalWarnings warnings={warnings} />
    </div>
  );
}

function RenderPrecedent({ evts }: { evts: TelemetryEvent[] }) {
  if (evts.length === 0) return null;
  const ps = evts[evts.length - 1].payload_summary;
  const count = (ps.count as number) ?? (ps.precedent_count as number) ?? 0;
  const mix = ps.feedback_mix as Record<string, number> | undefined;
  return (
    <div>
      <h3 style={sectionTitle}>Precedent Search</h3>
      <KV label="Precedents Found" value={String(count)} />
      {mix &&
        Object.entries(mix).map(([k, v]) => (
          <div key={k} style={kvRow}>
            <span style={kvLabel}>{k}</span>
            <span
              style={{
                color:
                  k === "positive"
                    ? "#4ade80"
                    : k === "negative"
                      ? "#f87171"
                      : "#facc15",
                fontWeight: 600,
                fontSize: 13,
              }}
            >
              {v}
            </span>
          </div>
        ))}
    </div>
  );
}

function RenderAuthz({ evts }: { evts: TelemetryEvent[] }) {
  if (evts.length === 0) return null;
  const ps = evts[evts.length - 1].payload_summary;
  const allowed = ps.allowed as boolean | undefined;
  const denied = ps.denied_concepts as string[] | undefined;
  return (
    <div>
      <h3 style={sectionTitle}>Authorization</h3>
      <div
        style={{
          display: "inline-block",
          padding: "4px 12px",
          borderRadius: 6,
          fontWeight: 700,
          fontSize: 14,
          background: allowed === false ? "#f871711a" : "#4ade801a",
          color: allowed === false ? "#f87171" : "#4ade80",
          marginBottom: 8,
        }}
      >
        {allowed === false ? "DENIED" : "ALLOWED"}
      </div>
      {denied && denied.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <p style={{ color: "#a3a3a3", fontSize: 12, margin: "0 0 4px" }}>
            Denied concepts:
          </p>
          {denied.map((c) => (
            <span
              key={c}
              style={{
                display: "inline-block",
                background: "#f871711a",
                color: "#f87171",
                fontSize: 12,
                padding: "2px 8px",
                borderRadius: 4,
                marginRight: 4,
                marginBottom: 4,
              }}
            >
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function RenderBuildPlan({ evts }: { evts: TelemetryEvent[] }) {
  if (evts.length === 0) return null;
  const ps = evts[evts.length - 1].payload_summary;
  const targets = ps.targets as string[] | undefined;
  const steps = (ps.plan_steps as number) ?? (ps.step_count as number) ?? 0;
  return (
    <div>
      <h3 style={sectionTitle}>Build Plan</h3>
      <KV label="Steps" value={String(steps)} />
      {targets && targets.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <p style={{ color: "#a3a3a3", fontSize: 12, margin: "0 0 4px" }}>
            Targets:
          </p>
          {targets.map((t) => (
            <span
              key={t}
              style={{
                display: "inline-block",
                background: "#262626",
                color: "#e5e5e5",
                fontSize: 12,
                padding: "2px 8px",
                borderRadius: 4,
                marginRight: 4,
                marginBottom: 4,
              }}
            >
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function RenderPersistTrace({ evts }: { evts: TelemetryEvent[] }) {
  if (evts.length === 0) return null;
  const e = evts[evts.length - 1];
  return (
    <div>
      <h3 style={sectionTitle}>Persist Trace</h3>
      <KV
        label="Latency"
        value={e.latency_ms != null ? `${e.latency_ms.toFixed(1)}ms` : "--"}
      />
    </div>
  );
}

function RenderEnd({ evts }: { evts: TelemetryEvent[] }) {
  if (evts.length === 0) return null;
  const ps = evts[evts.length - 1].payload_summary;
  const conf = ps.confidence_breakdown as ConfidenceBreakdown | undefined;
  const src = ps.source_attribution as Record<string, unknown> | undefined;
  return (
    <div>
      <h3 style={sectionTitle}>Resolution Result</h3>
      {conf && <ConfidenceBars confidence={conf} />}
      {!conf && ps.overall_confidence != null && (
        <KV
          label="Overall Confidence"
          value={`${((ps.overall_confidence as number) * 100).toFixed(0)}%`}
        />
      )}
      {src && (
        <div style={{ marginTop: 12 }}>
          <p
            style={{
              color: "#a3a3a3",
              fontSize: 12,
              margin: "0 0 6px",
              fontWeight: 600,
            }}
          >
            Source Attribution
          </p>
          {Object.entries(src).map(([k, v]) => (
            <KV key={k} label={k} value={String(v)} />
          ))}
        </div>
      )}
    </div>
  );
}

export function DetailPanel({ selectedStage, events }: DetailPanelProps) {
  if (!selectedStage) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "#6b7280",
          fontSize: 14,
        }}
      >
        Select a stage to see details
      </div>
    );
  }

  const evts = stageEvents(events, selectedStage);

  const containerStyle: CSSProperties = {
    padding: 16,
    overflowY: "auto",
    height: "100%",
  };

  return (
    <div style={containerStyle}>
      {selectedStage === "resolution_start" && <RenderStart evts={evts} />}
      {selectedStage === "parse_intent" && <RenderParseIntent evts={evts} />}
      {selectedStage === "resolve_concept" && (
        <RenderResolveConcept evts={evts} />
      )}
      {selectedStage === "tribal_check" && <RenderTribalCheck evts={evts} />}
      {selectedStage === "precedent" && <RenderPrecedent evts={evts} />}
      {selectedStage === "authz" && <RenderAuthz evts={evts} />}
      {selectedStage === "build_plan" && <RenderBuildPlan evts={evts} />}
      {selectedStage === "persist_trace" && <RenderPersistTrace evts={evts} />}
      {selectedStage === "resolution_end" && <RenderEnd evts={evts} />}
    </div>
  );
}
