# Deployment Guide — Neon + Aura + Render

ECP runs as a FastAPI web service on Render, talking to **Neon** (Postgres+pgvector) and **Neo4j AuraDB** (knowledge graph) over public TLS. Redis is **not** used for single-instance demo deploys — the in-process caches in ECP's clients are sufficient.

Target cost: **$0/month** on free tiers (Render web free, Neon free, Aura Free, Voyage embeddings free).

---

## Architecture

| Component | Host | Why |
|---|---|---|
| Backend API (FastAPI) | **Render** — free web service (Docker) | Native `render.yaml` in repo |
| Postgres + pgvector | **Neon** — free | Serverless Postgres with `pgvector` natively |
| Neo4j | **Neo4j AuraDB** — free | Managed graph (1 DB, 200k nodes) |
| Embeddings | **Voyage AI** — free tier | `voyage-3-lite`, 512 dims, no credit card |
| Redis | *not deployed* | In-process caches only. Add when going multi-replica. |
| Keep-warm | **UptimeRobot** — free | 5-min ping on `/admin/keep-warm` prevents auto-pause |

---

## Step 1 — Provision databases (one-time)

### 1a. Neon (Postgres + pgvector)

1. Sign up at https://neon.tech with GitHub.
2. Create project → region closest to Render (`us-west-2` / Oregon works well).
3. Copy the **pooled** connection string:
   `postgresql://<user>:<pw>@ep-xxx-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require`
4. In the Neon SQL editor run: `CREATE EXTENSION IF NOT EXISTS vector;`
   (The `preDeployCommand` on Render will also try this, but running it yourself confirms the extension is available on your plan.)

### 1b. Neo4j AuraDB Free

1. Sign up at https://neo4j.com/cloud/aura-free
2. Create Free instance → **download the credentials `.txt` file when prompted** (the password is shown once).
3. Record:
   - `NEO4J_URI` → e.g. `neo4j+s://abc12345.databases.neo4j.io` (must be `neo4j+s://`, not `bolt://`)
   - `NEO4J_USERNAME` → usually `neo4j`
   - `NEO4J_PASSWORD` → from the downloaded file

### 1c. Voyage AI

Sign up at https://voyageai.com → create an API key. Free tier covers demo traffic easily.

---

## Step 2 — Deploy the Render blueprint

1. Push this branch to GitHub.
2. https://dashboard.render.com → **New → Blueprint** → pick the repo + branch.
3. Render auto-detects `render.yaml`. It will create one service (`ecp-api`) and **prompt for every secret marked `sync: false`**:

   | Key | Value |
   |---|---|
   | `ECP_POSTGRES_DSN` | pooled Neon DSN from §1a (must include `?sslmode=require`) |
   | `ECP_NEO4J_URI` | `neo4j+s://<id>.databases.neo4j.io` |
   | `ECP_NEO4J_USER` | usually `neo4j` |
   | `ECP_NEO4J_PASSWORD` | from the Aura credentials file |
   | `ECP_API_KEY` | **generate with `openssl rand -hex 32`** and keep safe — clients MUST send `x-ecp-api-key: <this>` on every request |
   | `ECP_VOYAGE_API_KEY` | Voyage key from §1c |
   | `ECP_ANTHROPIC_API_KEY` | *(optional)* only if you flip `ECP_RESOLUTION_MODE` to `intelligent` |

4. Click **Apply**. Render will:
   - Build the Docker image.
   - Run `preDeployCommand: python scripts/init_db.py` (idempotent — creates tables, enables pgvector, migrates vector dimension if the embedding provider changed).
   - Start the web service on `:8080`.

5. When Render shows the service as **live**, you have a public URL like `https://ecp-api.onrender.com`. The schema exists but the database has **no seed data yet** — see Step 3.

---

## Step 3 — Load demo seed data (one-time, from your laptop)

`init_db.py` creates the schema. `seed_data.py` loads demo fixtures (glossary terms, data contracts, tribal knowledge, metric definitions, the financial-services sample scenario).

`scripts/seed_remote.sh` is the official "reset the demo" wrapper — it validates env vars, refuses to run against `localhost`, shows a 5-second countdown, then runs `init_db.py` + `seed_data.py` against whatever `ECP_POSTGRES_DSN` and `ECP_NEO4J_*` point to.

```bash
export ECP_POSTGRES_DSN='postgresql://<user>:<pw>@<neon-host>/neondb?sslmode=require'
export ECP_NEO4J_URI='neo4j+s://<id>.databases.neo4j.io'
export ECP_NEO4J_USER='neo4j'
export ECP_NEO4J_PASSWORD='<aura-password>'
export ECP_VOYAGE_API_KEY='pa-...'       # optional; without it, vector search uses ILIKE fallback
export ECP_EMBEDDING_PROVIDER=voyage     # must match render.yaml
export ECP_EMBEDDING_DIM=512             # must match render.yaml

./scripts/seed_remote.sh
```

What you'll see:

```
seed_remote.sh — resetting demo data on REMOTE databases
Postgres DSN host : ep-xxx-pooler.us-west-2.aws.neon.tech
Neo4j URI         : neo4j+s://abc12345.databases.neo4j.io
Embedding provider: voyage
Embedding dim     : 512
...
[1/2] Initializing schema (idempotent)…
Schema created successfully (embedding_dim=512).
[2/2] Seeding fixtures…
PostgreSQL: 28 assets seeded.
Neo4j: 47 nodes created.
asset_vectors: 17 rows (17 with real embeddings).
Done. Remote demo data loaded.
```

Re-run `seed_remote.sh` any time to reset demo state between sessions. It TRUNCATE CASCADEs the Postgres assets and DETACH DELETEs every Neo4j node before re-inserting, so it is **destructive by design**. Do not point it at a production database.

> Alternative: run it as a Render one-off job via the dashboard ("Shell" tab → same export + run). Useful if your laptop can't reach Neon/Aura (it needs public egress in both directions).

---

## Step 4 — Verify the deploy

### Health check

```bash
export ECP_BASE_URL='https://ecp-api.onrender.com'
export ECP_API_KEY='<the hex you generated>'

curl -s "$ECP_BASE_URL/health" | jq .
```

Expected:

```json
{
  "status": "ok",
  "mode": "orchestrator",
  "demo_mode": true,
  "version": "3.0.0",
  "embedding_available": true
}
```

Readiness (checks every backend):

```bash
curl -s "$ECP_BASE_URL/health/ready" | jq .
```

Expected `status: "ready"` and `checks.graph=true`, `checks.registry=true`, `checks.vector=true`, `checks.traces=true`. `checks.opa` may be `false` — that's fine in the demo (OPA is not deployed; fail-open is configured via `ECP_OPA_DEFAULT_ALLOW=true`).

### Smoke-test the 5 MCP tools (maps 1:1 to the API)

```bash
# 1) resolve_concept — finance analyst sees net_revenue + region_apac_finance
RESOLVE=$(curl -s -X POST "$ECP_BASE_URL/api/v1/resolve" \
  -H "content-type: application/json" \
  -H "x-ecp-api-key: $ECP_API_KEY" \
  -H "x-ecp-user-id: demo_finance" \
  -H "x-ecp-department: finance" \
  -H "x-ecp-role: analyst" \
  -d '{"concept": "What was APAC revenue last quarter?"}')
echo "$RESOLVE" | jq '.resolution_id, .status, .resolved_concepts | keys, .confidence.overall'
RID=$(echo "$RESOLVE" | jq -r '.resolution_id')

# 2) execute_metric — runs the plan (dry-run if ECP_CUBE_API_URL unset)
curl -s -X POST "$ECP_BASE_URL/api/v1/execute" \
  -H "content-type: application/json" \
  -H "x-ecp-api-key: $ECP_API_KEY" \
  -H "x-ecp-user-id: demo_finance" \
  -d "{\"resolution_id\": \"$RID\"}" | jq '.provenance, .results | type'

# 3) report_feedback
curl -s -X POST "$ECP_BASE_URL/api/v1/feedback" \
  -H "content-type: application/json" \
  -H "x-ecp-api-key: $ECP_API_KEY" \
  -H "x-ecp-user-id: demo_finance" \
  -d "{\"resolution_id\": \"$RID\", \"feedback\": \"accepted\"}" | jq .

# 4) search_context
curl -s -X POST "$ECP_BASE_URL/api/v1/search" \
  -H "content-type: application/json" \
  -H "x-ecp-api-key: $ECP_API_KEY" \
  -H "x-ecp-user-id: demo_finance" \
  -d '{"query": "revenue", "limit": 5}' | jq '.results | length, .results[0].type'

# 5) get_provenance
curl -s "$ECP_BASE_URL/api/v1/provenance/$RID" \
  -H "x-ecp-api-key: $ECP_API_KEY" \
  -H "x-ecp-user-id: demo_finance" | jq '.original_query, .status, .confidence.overall'
```

All five should return 2xx with populated bodies. Persona differentiation: swap the headers to `x-ecp-department: sales, x-ecp-role: director` and re-run step 1 — the resolved concepts should shift from `net_revenue + region_apac_finance` to `gross_revenue + region_apac_sales`. This is the core of the demo.

---

## Rotate `ECP_API_KEY`

Because the key gates every request, rotation is a two-step flip:

1. Generate a new key: `openssl rand -hex 32`.
2. Render dashboard → `ecp-api` → **Environment** → edit `ECP_API_KEY` → paste new → **Save**. Render triggers a ~30s rolling restart.
3. Update every client:
   - Claude Desktop MCP config (`claude_desktop_config.example.json` → `ECP_API_KEY`).
   - Any curl scripts / dashboards / UptimeRobot custom-header config.
4. Optional: invalidate old resolution sessions by pointing at the new key only. Sessions in Postgres remain valid; only the auth header changes.

There is no "grace period" — old key stops working the moment Render finishes the restart. For a zero-downtime rotation you'd need two keys simultaneously active (not supported today; the code compares against a single `settings.api_key`).

---

## Monitoring & logs

- **Render logs**: dashboard → `ecp-api` → **Logs** tab. Live tail UI with search. Shows the startup banner, every request, and the per-DAG-step resolution trace.
- **CLI tail**: `render logs --service ecp-api --tail` (install from https://render.com/docs/cli).
- **What to watch for**:
  - `DEMO MODE — public sandbox` at startup → `ECP_DEMO_MODE=true` is active (expected).
  - `api_key_required= yes` at startup → confirms `ECP_API_KEY` is enforced.
  - `embeddings = voyage/voyage-3-lite (dim=512)` → Voyage key is wired.
  - `embeddings = voyage (ILIKE fallback)` → **`ECP_VOYAGE_API_KEY` is missing or wrong**. Search + precedent still work but use text match, not cosine.
  - 401 spikes → a client is missing / sending a stale `x-ecp-api-key`.
- **Aura monitoring**: https://console.neo4j.io → your instance → Metrics. Watch connection count; the free tier caps at low double digits.
- **Neon monitoring**: Neon dashboard → **Monitoring** tab. Watch connection count + compute seconds (free tier has a monthly compute-hour budget).
- **Synthetic uptime**: UptimeRobot free → add an HTTP(S) monitor on `$ECP_BASE_URL/admin/keep-warm` every 5 minutes. That endpoint pings every backend (graph, registry, vector, traces) on each call, so the whole stack stays warm.

---

## Cost estimate (current tier)

| Line item | Plan | Monthly cost |
|---|---|---|
| Render web service | Free (512MB, 0.1 CPU, sleeps after 15min idle) | **$0** |
| Neon Postgres | Free (0.5GB storage, 190 compute-hours/mo) | **$0** |
| Neo4j Aura | Free (1 DB, 200k nodes, auto-pause) | **$0** |
| Voyage AI embeddings | Free tier (50M tokens/month) | **$0** |
| Anthropic (optional intelligent mode) | Pay-as-you-go Haiku 4.5 | ~**$1–5** if used heavily |
| UptimeRobot | Free (50 monitors) | **$0** |
| **Total** | | **$0** (demo) / **~$5** (if Anthropic enabled) |

Upgrade thresholds you'll hit first:
- **Render free sleeps after 15 min idle** (30s cold-start). UptimeRobot keep-warm mitigates this during business hours; the `/admin/keep-warm` endpoint specifically pings every backend so Neon + Aura also stay warm. For no-cold-start SLAs → Render Starter at ~$7/mo.
- **Neon free compute-hours** (190/mo). Each idle minute doesn't count; a busy demo day runs ~2–3 hours. Upgrade to Launch at $19/mo if you exhaust it.
- **Aura free auto-pauses after 3 days idle**. Click "resume" in the console, or ping `/admin/keep-warm` regularly. Professional tier starts at ~$65/mo for always-on.

---

## Security note — DEMO-ONLY posture

This deployment intentionally runs in demo mode:

- `ECP_OPA_DEFAULT_ALLOW=true` — fail-open authorization, because there is no OPA sidecar deployed. **Production deploys must run OPA and set `ECP_OPA_DEFAULT_ALLOW=false`.**
- `ECP_DEMO_MODE=true` — permissive CORS (`allow_origins=*`) so the demo UI on Vercel / GitHub Pages can call this API from a browser.
- `ECP_API_KEY` **is enforced** (every request must send `x-ecp-api-key`), so the public Render URL is not an open API. Without the key, all `/api/v1/*` routes return 401.

Never reuse this configuration for a production deployment. The combination of wide-open CORS, fail-open authorization, and a single shared API key is appropriate for a controlled demo handoff, not for anything storing real data.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/health/ready` returns `checks.registry=false` | `ECP_POSTGRES_DSN` missing `?sslmode=require`, or pgvector extension not created | Re-run `CREATE EXTENSION vector;` in Neon SQL editor; verify DSN has `?sslmode=require` |
| `/health/ready` returns `checks.graph=false` | Aura URI is `bolt://` instead of `neo4j+s://`, or password wrong | Aura requires TLS — use `neo4j+s://` |
| `POST /api/v1/resolve` returns 401 | `ECP_API_KEY` not set on request | Add `-H "x-ecp-api-key: <your-key>"`; check Render env tab has the value |
| Resolve returns `status: disambiguation_required` with no resolved concepts | Seed data not loaded | Run `./scripts/seed_remote.sh` |
| `embeddings = voyage (ILIKE fallback)` in startup logs | `ECP_VOYAGE_API_KEY` not set | Add the key in Render env; restart the service |
| First request after idle is slow (~30s) | Render free tier sleep | Expected; UptimeRobot keep-warm prevents it during business hours |
| Render build fails on `pip install -e .` | Dockerfile Python version mismatch | Check `pyproject.toml` required Python version matches the `python:3.11-slim` base |

---

## Local development (unchanged)

None of the above affects the local Docker Compose dev loop. For local iteration:

```bash
docker compose up -d
python scripts/init_db.py
python scripts/seed_data.py
uvicorn src.main:app --reload --port 8080
```

The `ECP_*` env vars default to `localhost:5432` / `bolt://localhost:7687` / no API key — all the Render-specific behavior is off unless you explicitly set the env vars.
