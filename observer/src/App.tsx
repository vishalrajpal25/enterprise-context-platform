import { useMemo, useState } from "react";
import { useTelemetryStream } from "./useTelemetryStream";
import type { TelemetryEvent } from "./types/events";
import { ResolutionFlow } from "./components/ResolutionFlow";
import { DetailPanel } from "./components/DetailPanel";
import { RecentResolutions } from "./components/RecentResolutions";

const ECP_BASE_URL =
  (import.meta.env.VITE_ECP_BASE_URL as string | undefined) ?? "";
const ECP_API_KEY =
  (import.meta.env.VITE_ECP_API_KEY as string | undefined) ?? "";

function latestResolutionId(events: TelemetryEvent[]): string | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    if (events[i].stage === "resolution_start")
      return events[i].resolution_id;
  }
  return events[events.length - 1]?.resolution_id ?? null;
}

function personaFromEvents(events: TelemetryEvent[]): string | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    if (events[i].stage === "resolution_start") {
      const ps = events[i].payload_summary;
      const user = ps.user_id as string | undefined;
      const dept = ps.department as string | undefined;
      if (user || dept) {
        return [user, dept].filter(Boolean).join(" / ");
      }
    }
  }
  return null;
}

export default function App() {
  const { events, state } = useTelemetryStream({
    baseUrl: ECP_BASE_URL,
    apiKey: ECP_API_KEY || undefined,
  });

  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [selectedResolutionId, setSelectedResolutionId] = useState<
    string | null
  >(null);

  const activeId = selectedResolutionId ?? latestResolutionId(events);
  const currentEvents = useMemo(
    () => (activeId ? events.filter((e) => e.resolution_id === activeId) : []),
    [events, activeId],
  );

  const persona = useMemo(() => personaFromEvents(currentEvents), [currentEvents]);

  const handleSelectResolution = (id: string) => {
    setSelectedResolutionId(id);
    setSelectedStage(null);
  };

  return (
    <div
      style={{
        fontFamily:
          "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        background: "#0f0f0f",
        color: "#e5e5e5",
        height: "100vh",
        display: "grid",
        gridTemplateRows: "60px 1fr 80px",
        gridTemplateColumns: "55% 45%",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <header
        style={{
          gridColumn: "1 / -1",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 20px",
          borderBottom: "1px solid #262626",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <h1 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
            ECP Resolution Observer
          </h1>
          {persona && (
            <span
              style={{
                fontSize: 12,
                color: "#a3a3a3",
                background: "#1a1a1a",
                padding: "3px 10px",
                borderRadius: 6,
                border: "1px solid #333",
              }}
            >
              {persona}
            </span>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {state === "reconnecting" && (
            <span style={{ fontSize: 12, color: "#fb923c" }}>
              Reconnecting...
            </span>
          )}
          <ConnectionBadge state={state} />
        </div>
      </header>

      {/* Left: Resolution Flow */}
      <div
        style={{
          padding: 16,
          overflowY: "auto",
          borderRight: "1px solid #262626",
        }}
      >
        {currentEvents.length > 0 ? (
          <ResolutionFlow
            events={currentEvents}
            selectedStage={selectedStage}
            onSelectStage={setSelectedStage}
          />
        ) : (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "#6b7280",
              fontSize: 13,
            }}
          >
            <p>
              Fire a resolution from Claude Desktop or{" "}
              <code style={{ background: "#1a1a1a", padding: "2px 6px", borderRadius: 4 }}>
                scripts/demo.py
              </code>{" "}
              to see stages light up here.
            </p>
          </div>
        )}
      </div>

      {/* Right: Detail Panel */}
      <div
        style={{
          padding: 0,
          overflowY: "auto",
          background: "#141414",
        }}
      >
        <DetailPanel selectedStage={selectedStage} events={currentEvents} />
      </div>

      {/* Bottom: Recent Resolutions */}
      <div
        style={{
          gridColumn: "1 / -1",
          padding: "0 16px",
          borderTop: "1px solid #262626",
          background: "#0f0f0f",
          overflowX: "auto",
        }}
      >
        <RecentResolutions
          events={events}
          selectedId={activeId}
          onSelect={handleSelectResolution}
        />
      </div>
    </div>
  );
}

function ConnectionBadge({ state }: { state: string }) {
  const color =
    state === "open"
      ? "#4ade80"
      : state === "reconnecting"
        ? "#fb923c"
        : "#6b7280";
  return (
    <span
      style={{
        border: `1px solid ${color}`,
        color,
        padding: "3px 10px",
        borderRadius: 999,
        fontSize: 11,
        textTransform: "uppercase",
        letterSpacing: 0.5,
        fontWeight: 600,
      }}
    >
      {state}
    </span>
  );
}
