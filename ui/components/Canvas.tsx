"use client";

import { useStore } from "@/lib/store";
import { findIndustryForWorld } from "@/lib/worlds";
import { Composer } from "./Composer";
import { Controls } from "./Controls";
import { ResolutionStory } from "./ResolutionStory";

export function Canvas() {
  const { world } = useStore();
  const industry = findIndustryForWorld(world.id);

  return (
    <main className="flex-1 overflow-y-auto">
      <div className="max-w-[1100px] mx-auto px-10 pt-6 pb-10">
        {/* Compact header — breadcrumb + company + tagline, tightly stacked */}
        <div className="mb-4">
          <div className="flex items-center gap-2 text-label uppercase tracking-[0.14em] font-semibold">
            <span className="text-accent">{industry.name}</span>
            <span className="text-hairline-strong">/</span>
            <span className="text-muted">{world.kind}</span>
          </div>
          <div className="mt-1 flex items-baseline gap-3 flex-wrap">
            <h1 className="serif text-[26px] leading-[32px] font-semibold text-ink">
              {world.name}
            </h1>
            <p className="text-label text-muted italic">
              {world.tagline}
            </p>
          </div>
        </div>

        {/* Controls strip — one line */}
        <div className="pb-4 mb-5 border-b border-hairline">
          <Controls />
        </div>

        {/* Composer */}
        <div className="mb-8">
          <Composer />
        </div>

        <ResolutionStory />
      </div>
    </main>
  );
}
