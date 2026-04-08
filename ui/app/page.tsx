"use client";

import { useState } from "react";
import { Topbar, type ViewMode } from "@/components/Topbar";
import { StepsStrip } from "@/components/StepsStrip";
import { LeftRail } from "@/components/LeftRail";
import { Canvas } from "@/components/Canvas";
import { StoreProvider } from "@/lib/store";

export default function Page() {
  const [view, setView] = useState<ViewMode>("business");
  return (
    <StoreProvider>
      <div className="h-screen flex flex-col">
        <Topbar view={view} onViewChange={setView} />
        <StepsStrip />
        <div className="flex flex-1 min-h-0">
          <LeftRail />
          <Canvas />
        </div>
      </div>
    </StoreProvider>
  );
}
