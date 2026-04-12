"use client";

import { ArrowUp, Loader2, Pencil } from "lucide-react";
import { useRef, useEffect, useState } from "react";
import { useStore } from "@/lib/store";
import clsx from "clsx";

/**
 * Question input with clear edit affordance.
 * Shows the pre-filled question as readable text with a pencil icon.
 * Click anywhere on the text or the pencil to focus the editor.
 */
export function Composer() {
  const { question, setQuestion, run, status } = useStore();
  const loading = status === "loading";
  const canRun = !loading && !!question.trim();
  const ref = useRef<HTMLTextAreaElement>(null);
  const [focused, setFocused] = useState(false);

  // Auto-grow textarea as content changes.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [question]);

  return (
    <div>
      {/* Label */}
      <div className="flex items-center gap-2 mb-2">
        <label className="text-label uppercase tracking-[0.12em] font-semibold text-muted">
          Question
        </label>
        <button
          onClick={() => ref.current?.focus()}
          className="text-muted hover:text-ink transition-colors"
          aria-label="Edit question"
        >
          <Pencil size={12} />
        </button>
      </div>

      {/* Input surface */}
      <div
        onClick={() => ref.current?.focus()}
        className={clsx(
          "flex items-end gap-3 bg-surface border-2 transition-colors cursor-text",
          focused
            ? "border-accent shadow-[0_0_0_1px_rgba(31,77,216,0.15)]"
            : "border-hairline hover:border-hairline-strong",
          "px-5 py-3",
        )}
      >
        <textarea
          ref={ref}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (canRun) run();
            }
          }}
          rows={1}
          placeholder="Ask a business question…"
          className={clsx(
            "flex-1 resize-none bg-transparent text-[16px] leading-[24px]",
            "text-ink placeholder:text-muted/60 placeholder:italic",
            "focus:outline-none overflow-hidden",
          )}
          style={{ minHeight: "24px" }}
        />

        <button
          onClick={(e) => {
            e.stopPropagation();
            run();
          }}
          disabled={!canRun}
          className={clsx(
            "shrink-0 w-8 h-8 flex items-center justify-center transition-all",
            canRun
              ? "bg-accent text-white hover:bg-ink"
              : "bg-elevated text-muted cursor-not-allowed",
          )}
          aria-label="Resolve question"
        >
          {loading ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <ArrowUp size={14} strokeWidth={2.5} />
          )}
        </button>
      </div>
    </div>
  );
}
