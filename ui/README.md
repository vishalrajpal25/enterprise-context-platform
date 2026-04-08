# ECP Studio

The interactive sandbox for the Enterprise Context Platform. Shows how ECP
resolves a business question into a trusted, governed, auditable answer —
with every definition, fiscal rule, tribal warning, and policy decision
surfaced step by step.

**Stack:** Next.js 14 (App Router) · TypeScript · Tailwind · Framer Motion · Lucide.
**Design system:** "Graphite" — warm off-white canvas, white surface panels,
monochrome ink with a single restrained accent blue. Serif (Fraunces) for
headlines, Inter for UI, IBM Plex Mono for data.

## Run locally

```bash
cd ui
npm install
npm run dev
```

Open http://localhost:3000.

The UI works **with or without a backend**. It tries the ECP FastAPI at
`NEXT_PUBLIC_ECP_API_BASE` (default `http://localhost:8080`) with a short
timeout and silently falls back to a bundled mock resolver if anything
fails. The topbar shows a `live api` / `mock data` chip so you always know
which mode you're in.

Point it at a different backend:

```bash
NEXT_PUBLIC_ECP_API_BASE=https://ecp.example.com npm run dev
```

## What's in here

```
app/           Next.js App Router entry + global styles
components/    UI — Topbar, LeftRail, Canvas, Composer, DAG, ...
lib/           Typed API client, mock resolver, store, seed worlds
```

### Key components

- [components/Topbar.tsx](components/Topbar.tsx) — brand + tagline, live/mock chip, view toggle, theme
- [components/StepsStrip.tsx](components/StepsStrip.tsx) — dismissable one-line guidance
- [components/LeftRail.tsx](components/LeftRail.tsx) — Industry + Company navigator
- [components/Canvas.tsx](components/Canvas.tsx) — page shell
- [components/Controls.tsx](components/Controls.tsx) — Role + Scenario pill clusters
- [components/Composer.tsx](components/Composer.tsx) — chat-style question input
- [components/ResolutionStory.tsx](components/ResolutionStory.tsx) — the hero: headline, DAG, meaning, warnings, governance, precedents
- [components/DAG.tsx](components/DAG.tsx) — the full transparent resolution trace (per-step source / query / returned / selected)
- [components/Tile.tsx](components/Tile.tsx) — reusable framed section block with tone cues
- [lib/worlds.ts](lib/worlds.ts) — seed data: 3 industries × 5 companies × personas × scenarios
- [lib/mockResolver.ts](lib/mockResolver.ts) — hand-authored resolutions that mirror the real API shape
- [lib/api.ts](lib/api.ts) — live/mock fallback HTTP client
- [lib/store.tsx](lib/store.tsx) — React context + reducer for the whole app state

## Industries seeded

- **Finance** — Metro Capital (sell-side IB), Pine Ridge Capital (buy-side fund)
- **Healthcare** — Meridian Health (provider IDN), Atlas Health Plan (payer)
- **Technology** — Nimbus Cloud (SaaS)

The default path on first load is `Finance → Metro Capital → Finance Analyst → APAC revenue last quarter` — it auto-resolves so the first thing a visitor sees is a fully-rendered trace. Switching role to Sales Analyst re-resolves and shows the same question producing a different answer (the key aha moment).

## Build & deploy

```bash
npm run build     # static optimized build in .next/
npm run start     # serve the build
npm run typecheck # tsc --noEmit
```

Static export friendly — deploys to Vercel, Netlify, Cloudflare Pages, or
any static host with `NEXT_PUBLIC_ECP_API_BASE` set as a build-time env.
