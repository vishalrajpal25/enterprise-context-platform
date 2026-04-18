import type { TribalWarningPayload } from "../types/events";

interface TribalWarningsProps {
  warnings: TribalWarningPayload[];
}

function severityColor(severity: string): string {
  switch (severity.toLowerCase()) {
    case "high":
      return "#f87171";
    case "medium":
      return "#fb923c";
    default:
      return "#6b7280";
  }
}

export function TribalWarnings({ warnings }: TribalWarningsProps) {
  if (warnings.length === 0) {
    return (
      <p style={{ color: "#6b7280", fontSize: 13 }}>No tribal warnings.</p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {warnings.map((w) => (
        <div
          key={w.id}
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
              alignItems: "center",
              gap: 8,
              marginBottom: 6,
            }}
          >
            <span
              style={{
                background: severityColor(w.severity),
                color: "#fff",
                fontSize: 10,
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: 4,
                textTransform: "uppercase",
              }}
            >
              {w.severity}
            </span>
          </div>
          <p style={{ margin: "0 0 4px", fontSize: 13, color: "#e5e5e5" }}>
            {w.description}
          </p>
          <p style={{ margin: "0 0 4px", fontSize: 12, color: "#737373" }}>
            {w.impact}
          </p>
          <p
            style={{
              margin: 0,
              fontSize: 12,
              color: "#a3a3a3",
              fontStyle: "italic",
            }}
          >
            {w.workaround}
          </p>
        </div>
      ))}
    </div>
  );
}
