import { useEffect, useRef, useState, useCallback } from "react";
import type { TelemetryEvent } from "./types/events";

export type ConnectionState = "connecting" | "open" | "reconnecting" | "closed";

export interface UseTelemetryStreamOptions {
  baseUrl: string;
  apiKey?: string;
  resolutionId?: string;
  userId?: string;
  /** Polling interval in ms (default 2000). */
  pollIntervalMs?: number;
  /** For tests: inject a custom EventSource factory to use SSE instead of polling. */
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

const EVENT_BUFFER_CAP = 2000;
const DEFAULT_POLL_MS = 2000;

export function useTelemetryStream(
  options: UseTelemetryStreamOptions,
): UseTelemetryStreamResult {
  const {
    baseUrl,
    apiKey,
    resolutionId,
    userId,
    pollIntervalMs = DEFAULT_POLL_MS,
    eventSourceFactory,
  } = options;

  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [state, setState] = useState<ConnectionState>("connecting");
  const seqRef = useRef(0);

  const addEvents = useCallback((newEvents: TelemetryEvent[]) => {
    if (newEvents.length === 0) return;
    setEvents((prev) => {
      const combined = [...prev, ...newEvents];
      return combined.length > EVENT_BUFFER_CAP
        ? combined.slice(combined.length - EVENT_BUFFER_CAP)
        : combined;
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let eventSource: EventSourceLike | null = null;

    const buildPollUrl = () => {
      const params = new URLSearchParams();
      params.set("after", String(seqRef.current));
      if (userId) params.set("user_id", userId);
      if (resolutionId) params.set("resolution_id", resolutionId);
      if (apiKey) params.set("api_key", apiKey);
      return `${baseUrl.replace(/\/$/, "")}/api/v1/telemetry/poll?${params}`;
    };

    // ---- Polling mode (default, works on all hosting) ----
    const poll = async () => {
      if (cancelled) return;
      try {
        const resp = await fetch(buildPollUrl());
        if (!resp.ok) {
          setState("reconnecting");
          timer = setTimeout(poll, pollIntervalMs * 2);
          return;
        }
        const data = await resp.json();
        setState("open");
        seqRef.current = data.seq ?? seqRef.current;

        const telemetryEvents = (data.events ?? []).filter(
          (e: Record<string, unknown>) => e.resolution_id && e.stage,
        ) as TelemetryEvent[];

        addEvents(telemetryEvents);
      } catch {
        setState("reconnecting");
      }
      if (!cancelled) {
        timer = setTimeout(poll, pollIntervalMs);
      }
    };

    // ---- EventSource mode (for tests with injected factory) ----
    const connectEventSource = () => {
      if (cancelled) return;
      const params = new URLSearchParams();
      if (resolutionId) params.set("resolution_id", resolutionId);
      if (userId) params.set("user_id", userId);
      if (apiKey) params.set("api_key", apiKey);
      const qs = params.toString();
      const url = `${baseUrl.replace(/\/$/, "")}/api/v1/telemetry/stream${qs ? `?${qs}` : ""}`;

      const factory = eventSourceFactory!;
      eventSource = factory(url);

      eventSource.addEventListener("open", () => setState("open"));
      eventSource.addEventListener("message", (ev) => {
        try {
          const parsed = JSON.parse(ev.data);
          if (!parsed.resolution_id || !parsed.stage) return;
          addEvents([parsed as TelemetryEvent]);
        } catch {
          // skip
        }
      });
      eventSource.addEventListener("error", () => {
        if (cancelled) return;
        eventSource?.close();
        eventSource = null;
        setState("reconnecting");
        timer = setTimeout(connectEventSource, 500);
      });
    };

    setState("connecting");
    if (eventSourceFactory) {
      connectEventSource();
    } else {
      poll();
    }

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
      eventSource?.close();
      setState("closed");
    };
  }, [baseUrl, apiKey, resolutionId, userId, pollIntervalMs, eventSourceFactory, addEvents]);

  const clear = useCallback(() => {
    setEvents([]);
    seqRef.current = 0;
  }, []);

  return { events, state, clear };
}
