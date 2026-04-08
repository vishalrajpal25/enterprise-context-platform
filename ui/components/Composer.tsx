"use client";

import { ArrowUp, Loader2 } from "lucide-react";
import { useRef, useEffect } from "react";
import { useStore } from "@/lib/store";
import clsx from "clsx";

/**
 * Chat-style input. Single-row by default, auto-grows on new lines.
 * The scenario pre-fills the question; the user can edit or replace it.
 * Submit button is integrated into the trailing edge.
 */
export function Composer() {
  const { question, setQuestion, run, status } = useStore();
  const loading = status === "loading";
  const canRun = !loading && !!question.trim();
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-grow textarea as content changes.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [question]);

  return (
    <div className="relative">
      {/* Input surface */}
      <div
        className={clsx(
          "flex items-end gap-3 bg-surface border transition-colors",
          "border-hairline-strong focus-within:border-ink",
          "px-5 py-3.5",
        )}
      >
        <textarea
          ref={ref}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (canRun) run();
            }
          }}
          rows={1}
          placeholder="Ask a business question…"
          className={clsx(
            "flex-1 resize-none bg-transparent serif text-[20px] leading-[28px]",
            "text-ink placeholder:text-muted/60 placeholder:italic",
            "focus:outline-none overflow-hidden",
          )}
          style={{ minHeight: "28px" }}
        />

        <button
          onClick={() => run()}
          disabled={!canRun}
          className={clsx(
            "shrink-0 w-9 h-9 flex items-center justify-center transition-all",
            canRun
              ? "bg-ink text-canvas hover:bg-accent"
              : "bg-elevated text-muted cursor-not-allowed",
          )}
          aria-label="Resolve question"
        >
          {loading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <ArrowUp size={16} strokeWidth={2.5} />
          )}
        </button>
      </div>

      {/* Hint below */}
      <div className="mt-2 text-label text-muted">
        <kbd className="font-mono">Enter</kbd> to resolve ·{" "}
        <kbd className="font-mono">Shift</kbd>+
        <kbd className="font-mono">Enter</kbd> for a new line
      </div>
    </div>
  );
}
