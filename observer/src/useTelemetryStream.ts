import { useEffect, useRef, useState } from "react";
import type { TelemetryEvent } from "./types/events";

export type ConnectionState = "connecting" | "open" | "reconnecting" | "closed";

export interface UseTelemetryStreamOptions {
  baseUrl: string;
  apiKey?: string;
  resolutionId?: string;
  userId?: string;
  eventSourceFactory?: (url: string) => EventSourceLike;
}

export interface EventSourceLike {
  close(): void;
  addEventListener(type: "message", listener: (ev: { data: string }) => void): void;
  addEventListener(type: "error", listener: () => void): void;
  addEventListener(type: "open", listener: () => void): void;
}

export interface UseTelemetryStreamResult {
  events: TelemetryEvent[];
  state: ConnectionState;
  clear: () => void;
}

const RECONNECT_DELAYS_MS = [250, 500, 1000, 2000, 5000];
const EVENT_BUFFER_CAP = 2000;

export function useTelemetryStream(
  options: UseTelemetryStreamOptions,
): UseTelemetryStreamResult {
  const { baseUrl, apiKey, resolutionId, userId, eventSourceFactory } = options;
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [state, setState] = useState<ConnectionState>("connecting");
  const attemptRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;
    let source: EventSourceLike | null = null;

    const buildUrl = () => {
      const params = new URLSearchParams();
      if (resolutionId) params.set("resolution_id", resolutionId);
      if (userId) params.set("user_id", userId);
      if (apiKey) params.set("api_key", apiKey);
      const qs = params.toString();
      return `${baseUrl.replace(/\/$/, "")}/api/v1/telemetry/stream${qs ? `?${qs}` : ""}`;
    };

    const connect = () => {
      if (cancelled) return;
      const url = buildUrl();
      const factory =
        eventSourceFactory ??
        ((u: string) => new EventSource(u) as unknown as EventSourceLike);
      source = factory(url);

      source.addEventListener("open", () => {
        attemptRef.current = 0;
        setState("open");
      });

      source.addEventListener("message", (ev) => {
        try {
          const parsed = JSON.parse(ev.data);
          // Skip heartbeats and connection confirmations — only buffer
          // real telemetry events that have a resolution_id and stage.
          if (!parsed.resolution_id || !parsed.stage) return;
          setEvents((prev) => {
            const next =
              prev.length >= EVENT_BUFFER_CAP
                ? prev.slice(prev.length - EVENT_BUFFER_CAP + 1)
                : prev;
            return [...next, parsed as TelemetryEvent];
          });
        } catch (err) {
          console.warn("telemetry stream: failed to parse event", err);
        }
      });

      source.addEventListener("error", () => {
        if (cancelled) return;
        setState("reconnecting");
        source?.close();
        source = null;
        const delay =
          RECONNECT_DELAYS_MS[
            Math.min(attemptRef.current, RECONNECT_DELAYS_MS.length - 1)
          ];
        attemptRef.current += 1;
        timerRef.current = setTimeout(connect, delay);
      });
    };

    setState("connecting");
    connect();

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      source?.close();
      setState("closed");
    };
  }, [baseUrl, apiKey, resolutionId, userId, eventSourceFactory]);

  const clear = () => setEvents([]);

  return { events, state, clear };
}
