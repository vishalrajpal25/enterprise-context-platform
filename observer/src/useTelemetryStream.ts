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

const RECONNECT_DELAYS_MS = [500, 1000, 2000, 3000, 5000];
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
    let abortController: AbortController | null = null;
    let eventSource: EventSourceLike | null = null;

    const buildUrl = () => {
      const params = new URLSearchParams();
      if (resolutionId) params.set("resolution_id", resolutionId);
      if (userId) params.set("user_id", userId);
      if (apiKey) params.set("api_key", apiKey);
      const qs = params.toString();
      return `${baseUrl.replace(/\/$/, "")}/api/v1/telemetry/stream${qs ? `?${qs}` : ""}`;
    };

    const addEvent = (parsed: TelemetryEvent) => {
      setEvents((prev) => {
        const next =
          prev.length >= EVENT_BUFFER_CAP
            ? prev.slice(prev.length - EVENT_BUFFER_CAP + 1)
            : prev;
        return [...next, parsed];
      });
    };

    const scheduleReconnect = () => {
      if (cancelled) return;
      setState("reconnecting");
      const delay =
        RECONNECT_DELAYS_MS[
          Math.min(attemptRef.current, RECONNECT_DELAYS_MS.length - 1)
        ];
      attemptRef.current += 1;
      timerRef.current = setTimeout(connect, delay);
    };

    // fetch-based SSE reader — survives connection drops better than EventSource
    const connectWithFetch = async () => {
      if (cancelled) return;
      abortController = new AbortController();

      try {
        const resp = await fetch(buildUrl(), {
          signal: abortController.signal,
          headers: { Accept: "text/event-stream" },
        });

        if (!resp.ok || !resp.body) {
          scheduleReconnect();
          return;
        }

        setState("open");
        attemptRef.current = 0;

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          if (cancelled) break;
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const part of parts) {
            const trimmed = part.trim();
            if (!trimmed || trimmed.startsWith(":")) continue;
            const dataPrefix = "data: ";
            const dataLine = trimmed
              .split("\n")
              .find((l) => l.startsWith(dataPrefix));
            if (!dataLine) continue;

            try {
              const parsed = JSON.parse(dataLine.slice(dataPrefix.length));
              if (!parsed.resolution_id || !parsed.stage) continue;
              addEvent(parsed as TelemetryEvent);
            } catch {
              // skip unparseable frames
            }
          }
        }
      } catch (err) {
        if (cancelled) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
      }

      if (!cancelled) scheduleReconnect();
    };

    // EventSource path — used when a custom factory is provided (tests)
    const connectWithEventSource = () => {
      if (cancelled) return;
      const url = buildUrl();
      const factory = eventSourceFactory!;
      eventSource = factory(url);

      eventSource.addEventListener("open", () => {
        attemptRef.current = 0;
        setState("open");
      });

      eventSource.addEventListener("message", (ev) => {
        try {
          const parsed = JSON.parse(ev.data);
          if (!parsed.resolution_id || !parsed.stage) return;
          addEvent(parsed as TelemetryEvent);
        } catch {
          // skip
        }
      });

      eventSource.addEventListener("error", () => {
        if (cancelled) return;
        eventSource?.close();
        eventSource = null;
        scheduleReconnect();
      });
    };

    const connect = () => {
      if (cancelled) return;
      if (eventSourceFactory) {
        connectWithEventSource();
      } else {
        connectWithFetch();
      }
    };

    setState("connecting");
    connect();

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      abortController?.abort();
      eventSource?.close();
      setState("closed");
    };
  }, [baseUrl, apiKey, resolutionId, userId, eventSourceFactory]);

  const clear = () => setEvents([]);

  return { events, state, clear };
}
