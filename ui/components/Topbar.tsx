"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { api, type HealthResponse } from "@/lib/api";
import clsx from "clsx";

type ViewMode = "business" | "technical";

export function Topbar({
  view,
  onViewChange,
}: {
  view: ViewMode;
  onViewChange: (v: ViewMode) => void;
}) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [live, setLive] = useState<"live" | "mock">("mock");
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved =
      typeof window !== "undefined"
        ? localStorage.getItem("ecp-theme")
        : null;
    if (saved === "dark") {
      document.documentElement.classList.add("dark");
      setDark(true);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const h = await api.health();
        if (!cancelled) {
          setHealth(h);
          setLive("live");
        }
      } catch {
        if (!cancelled) {
          setHealth(null);
          setLive("mock");
        }
      }
    };
    tick();
    const id = setInterval(tick, 15_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("ecp-theme", next ? "dark" : "light");
  };

  return (
    <header className="flex items-center justify-between px-6 h-14 shrink-0 bg-surface dark:bg-surface-dark border-b border-hairline-strong dark:border-hairline-dark">
      {/* Left: wordmark + mode chip */}
      <div className="flex items-center gap-5">
        <div className="flex items-baseline gap-3">
          <div className="flex items-baseline gap-2">
            <span className="serif text-[22px] font-semibold tracking-tight text-ink dark:text-ink-dark">
              ECP
            </span>
            <span className="text-label uppercase tracking-[0.16em] text-muted font-semibold">
              Studio
            </span>
          </div>
          <span className="hidden md:inline text-hairline-strong">·</span>
          <span className="hidden md:inline text-label text-muted italic">
            the meaning layer for enterprise AI
          </span>
        </div>
        <div
          className={clsx(
            "hidden md:inline-flex items-center gap-1.5 px-2 py-0.5 border text-label",
            live === "live"
              ? "border-ok text-ok"
              : "border-hairline dark:border-hairline-dark text-muted",
          )}
          title={
            live === "live"
              ? `Connected to live API · ${health?.mode || "orchestrator"}`
              : "Running on the bundled mock resolver. Start the API to see live data."
          }
        >
          <span
            className={clsx(
              "w-1.5 h-1.5 rounded-full",
              live === "live" ? "bg-ok" : "bg-muted",
            )}
          />
          {live === "live" ? "live api" : "mock data"}
        </div>
      </div>

      {/* Right: view toggle + theme */}
      <div className="flex items-center gap-3">
        <div className="flex items-center border border-hairline dark:border-hairline-dark">
          {(["business", "technical"] as const).map((v) => (
            <button
              key={v}
              onClick={() => onViewChange(v)}
              className={clsx(
                "px-3 py-1 text-label uppercase tracking-wider transition-colors",
                view === v
                  ? "bg-ink text-canvas dark:bg-ink-dark dark:text-canvas-dark"
                  : "text-muted hover:text-ink dark:hover:text-ink-dark",
              )}
            >
              {v}
            </button>
          ))}
        </div>
        <button
          onClick={toggleTheme}
          className="p-1.5 text-muted hover:text-ink dark:hover:text-ink-dark"
          aria-label="Toggle theme"
        >
          {dark ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}

export type { ViewMode };
