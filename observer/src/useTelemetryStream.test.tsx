import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { EventSourceLike } from "./useTelemetryStream";
import { useTelemetryStream } from "./useTelemetryStream";

function makeFakeSource() {
  const listeners: Record<string, Array<(ev: unknown) => void>> = {
    message: [],
    error: [],
    open: [],
  };
  const fake: EventSourceLike & {
    emit: (type: "message" | "error" | "open", ev?: unknown) => void;
    closed: boolean;
    url: string;
  } = {
    url: "",
    closed: false,
    addEventListener(type: string, listener: (ev: never) => void) {
      listeners[type] ??= [];
      listeners[type].push(listener as (ev: unknown) => void);
    },
    close() {
      fake.closed = true;
    },
    emit(type, ev) {
      listeners[type]?.forEach((l) => l(ev));
    },
  };
  return fake;
}

describe("useTelemetryStream", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("parses SSE messages into TelemetryEvent objects", async () => {
    const fake = makeFakeSource();
    const factory = vi.fn((url: string) => {
      fake.url = url;
      return fake;
    });

    const { result } = renderHook(() =>
      useTelemetryStream({
        baseUrl: "http://localhost:8080",
        eventSourceFactory: factory,
      }),
    );

    act(() => {
      fake.emit("open");
      fake.emit("message", {
        data: JSON.stringify({
          resolution_id: "rs_1",
          stage: "parse_intent",
          status: "ok",
          latency_ms: 2.4,
          payload_summary: { query: "apac" },
          ts: "2026-04-16T00:00:00Z",
        }),
      });
    });

    await waitFor(() => expect(result.current.events).toHaveLength(1));
    expect(result.current.state).toBe("open");
    expect(result.current.events[0].resolution_id).toBe("rs_1");
    expect(fake.url).toContain("/api/v1/telemetry/stream");
  });

  it("forwards resolution_id and api_key as query params", () => {
    const fake = makeFakeSource();
    const factory = vi.fn((url: string) => {
      fake.url = url;
      return fake;
    });

    renderHook(() =>
      useTelemetryStream({
        baseUrl: "http://localhost:8080",
        apiKey: "secret-key",
        resolutionId: "rs_xyz",
        eventSourceFactory: factory,
      }),
    );

    expect(fake.url).toContain("resolution_id=rs_xyz");
    expect(fake.url).toContain("api_key=secret-key");
  });

  it("reconnects with backoff on error", async () => {
    vi.useFakeTimers();
    const fakes: ReturnType<typeof makeFakeSource>[] = [];
    const factory = vi.fn(() => {
      const f = makeFakeSource();
      fakes.push(f);
      return f;
    });

    const { result } = renderHook(() =>
      useTelemetryStream({
        baseUrl: "http://localhost:8080",
        eventSourceFactory: factory,
      }),
    );

    act(() => {
      fakes[0].emit("error");
    });
    expect(result.current.state).toBe("reconnecting");
    expect(fakes[0].closed).toBe(true);

    await act(async () => {
      vi.advanceTimersByTime(600);
    });
    expect(factory).toHaveBeenCalledTimes(2);
    act(() => {
      fakes[1].emit("open");
    });
    expect(result.current.state).toBe("open");
  });

  it("ignores malformed SSE frames rather than crashing", async () => {
    const fake = makeFakeSource();
    const factory = vi.fn(() => fake);

    const { result } = renderHook(() =>
      useTelemetryStream({
        baseUrl: "http://localhost:8080",
        eventSourceFactory: factory,
      }),
    );

    act(() => {
      fake.emit("message", { data: "not valid json {{{" });
    });

    expect(result.current.events).toHaveLength(0);
  });
});
