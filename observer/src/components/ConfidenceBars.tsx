import type { ConfidenceBreakdown } from "../types/events";

interface ConfidenceBarsProps {
  confidence: ConfidenceBreakdown;
}

const FIELDS: { key: keyof ConfidenceBreakdown; label: string }[] = [
  { key: "definition", label: "Definition" },
  { key: "data_quality", label: "Data Quality" },
  { key: "temporal_validity", label: "Temporal Validity" },
  { key: "authorization", label: "Authorization" },
  { key: "completeness", label: "Completeness" },
  { key: "overall", label: "Overall" },
];

function barColor(value: number): string {
  if (value > 0.8) return "#4ade80";
  if (value >= 0.5) return "#facc15";
  return "#f87171";
}

export function ConfidenceBars({ confidence }: ConfidenceBarsProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {FIELDS.map(({ key, label }) => {
        const value = confidence[key];
        const isOverall = key === "overall";
        return (
          <div
            key={key}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span
              style={{
                width: 120,
                fontSize: isOverall ? 13 : 12,
                fontWeight: isOverall ? 700 : 400,
                color: isOverall ? "#e5e5e5" : "#a3a3a3",
                flexShrink: 0,
              }}
            >
              {label}
            </span>
            <div
              style={{
                flex: 1,
                height: isOverall ? 14 : 10,
                background: "#262626",
                borderRadius: 4,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${Math.min(value * 100, 100)}%`,
                  height: "100%",
                  background: barColor(value),
                  borderRadius: 4,
                  transition: "width 300ms ease",
                }}
              />
            </div>
            <span
              style={{
                width: 40,
                textAlign: "right",
                fontSize: isOverall ? 13 : 12,
                fontWeight: isOverall ? 700 : 400,
                color: barColor(value),
                flexShrink: 0,
              }}
            >
              {(value * 100).toFixed(0)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
