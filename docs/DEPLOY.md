# Free-Tier Deployment Guide

Target: shareable public demo at `$0/month` (modulo ~$5 lifetime spend on embeddings if you pick OpenAI; Voyage is free).

## Architecture (what runs where)

| Component | Host | Plan | Why |
|---|---|---|---|
| Backend API (FastAPI, this repo) | **Render** | Free web service (Docker) | Native `render.yaml` already in repo |
| Postgres + pgvector | **Neon** | Free | Serverless, supports `pgvector` extension |
| Neo4j | **Neo4j AuraDB** | Free | Official managed free tier (1 DB, 200k nodes) |
| Redis (optional) | **Upstash** | Free | Only needed if you enable caching |
| UI (Next.js) | **Vercel** | Hobby (free) | Zero-config Next.js deploys |
| Keep-warm pings | **UptimeRobot** | Free | 5-min HTTP check → prevents Render/Neon/Aura auto-pause |

Total cost: **$0/month**. The only thing that ever costs money is OpenAI embeddings *if* you choose that provider. Voyage (default) is free.

---

## Step 1 — Provision databases

### 1a. Neon (Postgres + pgvector)
1. Sign up at https://neon.tech with GitHub.
2. Create project → region closest to Render (Oregon/US-West works well).
3. Copy the **pooled** connection string. It looks like:
   `postgresql://user:pass@ep-xxx-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require`
4. In the Neon SQL editor run: `CREATE EXTENSION IF NOT EXISTS vector;`

### 1b. Neo4j AuraDB Free
1. Sign up at https://neo4j.com/cloud/aura-free
2. Create Free instance → **download the `.txt` credentials file when prompted** (you only see the password once).
3. Note:
   - `NEO4J_URI` — e.g. `neo4j+s://abc12345.databases.neo4j.io`
   - `NEO4J_USERNAME` — `neo4j`
   - `NEO4J_PASSWORD` — from credentials file

### 1c. (Optional) Upstash Redis
Skip unless you want caching. Sign up at https://upstash.com → create Redis DB → copy the `rediss://` URL.

---

## Step 2 — Get API keys

- **Voyage AI** (free, recommended for embeddings): https://voyageai.com → sign up → create API key.
- **Anthropic** (optional, only for `intelligent` resolution mode): https://console.anthropic.com

---

## Step 3 — Deploy backend to Render

1. Push this repo to GitHub (see "Clean checkin" section below).
2. Go to https://dashboard.render.com → **New → Blueprint** → connect your GitHub repo.
3. Render auto-detects `render.yaml` and creates the `ecp-api` service.
4. Before first deploy, add these **secret** env vars in the Render dashboard (Environment tab):

   | Key | Value |
   |---|---|
   | `ECP_POSTGRES_DSN` | Neon pooled DSN from step 1a |
   | `ECP_NEO4J_URI` | AuraDB URI from step 1b |
   | `ECP_NEO4J_USER` | `neo4j` |
   | `ECP_NEO4J_PASSWORD` | AuraDB password |
   | `ECP_VOYAGE_API_KEY` | Voyage key |
   | `ECP_ANTHROPIC_API_KEY` | *(optional)* |
   | `ECP_REDIS_URL` | *(optional, Upstash)* |

5. **First-run bootstrap**: flip these two in the dashboard, then trigger a manual deploy:
   - `ECP_BOOTSTRAP_DB=true`
   - `ECP_AUTO_SEED_DEMO=true`
6. Watch logs. When you see `seed complete`, hit `https://<your-service>.onrender.com/health` — it should return `demo_mode: true` and `status: healthy`.
7. **Flip both bootstrap flags back to `false`** and redeploy (otherwise every cold start re-seeds).

---

## Step 4 — Deploy UI to Vercel

1. Go to https://vercel.com/new → import the same GitHub repo.
2. **Root Directory**: `ui`
3. Framework preset: Next.js (auto-detected).
4. Add env var:
   - `NEXT_PUBLIC_ECP_API_BASE` = `https://<your-render-service>.onrender.com`
   - *(Optional)* `NEXT_PUBLIC_ECP_USE_LIVE=1` to hit the live backend instead of the mock. **Leave unset for the shareable demo** — the mock is richer, never flakes, and is what the Studio tiles are designed around.
5. Deploy. You'll get `https://<project>.vercel.app`.

---

## Step 5 — Keep-warm (critical for free tier)

Render free web services sleep after 15 min idle; Neon/Aura also auto-pause. One ping every 5 min keeps the whole stack warm.

1. Sign up at https://uptimerobot.com (free).
2. Add monitor → HTTP(S) → URL: `https://<your-render-service>.onrender.com/health`
3. Interval: 5 minutes.

That's it. The UI is now shareable; the backend is held warm by UptimeRobot.

---

## Clean checkin — before you push

```bash
# from repo root
git status
```

Make sure these are **not** staged (already ignored by `.gitignore`):
- `.next/`, `ui/.next/`, `ui/node_modules/`
- `.venv/`, `__pycache__/`
- `.env` (only `.env.example` should be committed)
- `TASK-positioning-update.md` — this is a scratch planning doc, decide whether to keep or delete before publishing

Recommended pre-push sanity:
```bash
ruff check src
pytest -q
cd ui && npm run typecheck && npm run build && cd ..
```

---

## What visitors see

- **UI link** (share this): `https://<project>.vercel.app` — the Studio sandbox, mock-first, always works.
- **API docs**: `https://<your-render-service>.onrender.com/docs` — FastAPI Swagger UI.
- **Health**: `https://<your-render-service>.onrender.com/health`

## Troubleshooting

- **Render build fails on `pip install -e .`** → check `pyproject.toml` Python version matches the 3.11-slim base; bump Dockerfile base if you've moved to 3.12.
- **`/health` returns `database: unhealthy`** → Neon DSN missing `sslmode=require`, or pgvector extension not created.
- **Neo4j connection refused** → AuraDB URI must start with `neo4j+s://` (encrypted), not `bolt://`.
- **UI shows CORS error when `NEXT_PUBLIC_ECP_USE_LIVE=1`** → ensure `ECP_DEMO_MODE=true` on Render (it opens CORS for the public demo). Already set in `render.yaml`.
- **Cold start is slow (~30s)** → expected on Render free tier for the first request after sleep; UptimeRobot prevents this during business hours.

## Security note

This deployment is **demo-grade**:
- `ECP_OPA_DEFAULT_ALLOW=true` (fail-open authorization)
- `ECP_DEMO_MODE=true` (permissive CORS)
- No `ECP_API_KEY` set (unauthenticated API)

**Never reuse these settings for anything real.** If you want to lock it down for a specific audience, set `ECP_API_KEY` on Render and add it as `NEXT_PUBLIC_ECP_API_KEY` to Vercel (and update `ui/lib/api.ts` to send the header).
