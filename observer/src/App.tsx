import { useMemo } from "react";
import { TimelinePanel } from "./components/TimelinePanel";
import { useTelemetryStream } from "./useTelemetryStream";
import type { TelemetryEvent } from "./types/events";

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

export default function App() {
  const { events, state } = useTelemetryStream({
    baseUrl: ECP_BASE_URL,
    apiKey: ECP_API_KEY || undefined,
  });

  const currentId = useMemo(() => latestResolutionId(events), [events]);
  const currentEvents = useMemo(
    () => (currentId ? events.filter((e) => e.resolution_id === currentId) : []),
    [events, currentId],
  );

  return (
    <div
      style={{
        fontFamily:
          "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        background: "#0f1115",
        color: "#e6eaf2",
        minHeight: "100vh",
        padding: 20,
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 18,
        }}
      >
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>
          ECP Observer{" "}
          <span style={{ color: "#6e7686", fontWeight: 400 }}>
            {"\u2014"} live resolutions
          </span>
        </h1>
        <ConnectionBadge state={state} />
      </header>
      <TimelinePanel resolutionId={currentId} events={currentEvents} />
      {state === "reconnecting" && <ReconnectBanner />}
      {!currentId && (
        <p style={{ color: "#6e7686", marginTop: 16, fontSize: 13 }}>
          Fire a resolution from Claude Desktop or{" "}
          <code>scripts/demo.py</code> to see stages light up here.
        </p>
      )}
    </div>
  );
}

function ConnectionBadge({ state }: { state: string }) {
  const color =
    state === "open"
      ? "#2f9e44"
      : state === "reconnecting"
        ? "#e67700"
        : "#6e7686";
  return (
    <span
      style={{
        background: "#1a1d24",
        border: `1px solid ${color}`,
        color,
        padding: "4px 10px",
        borderRadius: 999,
        fontSize: 12,
        textTransform: "uppercase",
        letterSpacing: 0.6,
      }}
    >
      {state}
    </span>
  );
}

function ReconnectBanner() {
  return (
    <div
      role="alert"
      style={{
        marginTop: 12,
        padding: "8px 12px",
        background: "#3a2a12",
        border: "1px solid #e67700",
        color: "#ffd8a8",
        borderRadius: 6,
        fontSize: 13,
      }}
    >
      Stream dropped {"\u2014"} attempting to reconnect{"\u2026"}
    </div>
  );
}
