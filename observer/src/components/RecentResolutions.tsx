import type { CSSProperties } from "react";
import type { TelemetryEvent } from "../types/events";

interface RecentResolutionsProps {
  events: TelemetryEvent[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

interface ResolutionSummary {
  id: string;
  concept: string;
  confidence: number | null;
  latencyMs: number | null;
  ts: string;
}

function buildSummaries(events: TelemetryEvent[]): ResolutionSummary[] {
  const byId: Record<string, TelemetryEvent[]> = {};
  for (const e of events) {
    if (!byId[e.resolution_id]) byId[e.resolution_id] = [];
    byId[e.resolution_id].push(e);
  }

  const summaries: ResolutionSummary[] = [];
  for (const [id, evts] of Object.entries(byId)) {
    const start = evts.find((e) => e.stage === "resolution_start");
    const end = evts.find(
      (e) => e.stage === "resolution_end" && e.status !== "started",
    );
    const concept = start
      ? String(
          start.payload_summary.concept ??
            start.payload_summary.query ??
            id.slice(0, 8),
        )
      : id.slice(0, 8);
    const confidence = end
      ? ((end.payload_summary.overall_confidence as number) ?? null)
      : null;
    const latencyMs = end
      ? ((end.payload_summary.total_latency_ms as number) ?? end.latency_ms ?? null)
      : null;
    const ts = start?.ts ?? evts[0]?.ts ?? "";
    summaries.push({ id, concept, confidence, latencyMs, ts });
  }

  return summaries.reverse();
}

function truncate(s: string, max: number): string {
  return s.length > max ? s.slice(0, max) + "\u2026" : s;
}

export function RecentResolutions({
  events,
  selectedId,
  onSelect,
}: RecentResolutionsProps) {
  const summaries = buildSummaries(events);

  const containerStyle: CSSProperties = {
    display: "flex",
    gap: 8,
    overflowX: "auto",
    padding: "8px 0",
    height: "100%",
    alignItems: "center",
  };

  return (
    <div style={containerStyle}>
      {summaries.length === 0 && (
        <span style={{ color: "#6b7280", fontSize: 12 }}>
          No resolutions yet
        </span>
      )}
      {summaries.map((s) => {
        const isSelected = s.id === selectedId;
        const confColor =
          s.confidence != null
            ? s.confidence > 0.8
              ? "#4ade80"
              : s.confidence >= 0.5
                ? "#facc15"
                : "#f87171"
            : "#6b7280";

        const pillStyle: CSSProperties = {
          flexShrink: 0,
          background: "#1a1a1a",
          border: isSelected ? "1px solid #e5e5e5" : "1px solid #333",
          borderRadius: 8,
          padding: "6px 12px",
          cursor: "pointer",
          display: "flex",
          flexDirection: "column",
          gap: 2,
          transition: "border 120ms",
          minWidth: 120,
          maxWidth: 200,
        };

        return (
          <div key={s.id} style={pillStyle} onClick={() => onSelect(s.id)}>
            <span
              style={{
                fontSize: 12,
                color: "#e5e5e5",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {truncate(s.concept, 40)}
            </span>
            <span style={{ fontSize: 11, color: confColor }}>
              {s.confidence != null
                ? `${(s.confidence * 100).toFixed(0)}%`
                : "pending"}
              {s.latencyMs != null && (
                <span style={{ color: "#6b7280", marginLeft: 6 }}>
                  {s.latencyMs.toFixed(0)}ms
                </span>
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
}
