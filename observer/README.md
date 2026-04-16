# ECP Observer

Live visualization of every Enterprise Context Platform resolution.
Subscribes to `GET /api/v1/telemetry/stream` (SSE) and renders pipeline
stages lighting up as they run.

**Separate deployable.** Own `package.json`, own `node_modules`, own build.

## Running locally

```bash
cd observer
npm install
npm run dev          # http://localhost:5174
```

Start ECP first:

```bash
docker compose up -d
python scripts/init_db.py && python scripts/seed_data.py
uvicorn src.main:app --reload --port 8080
```

Then run `python scripts/demo.py` to see stages light up.

## Configuration

```bash
# Point dev proxy at a different ECP instance
ECP_BASE_URL=https://ecp.example.com npm run dev

# Or set the browser-side URL directly
echo 'VITE_ECP_BASE_URL=https://ecp.example.com' > .env.local
```

## API key handling

When `ECP_API_KEY` is set, the observer passes it as `?api_key=...` since
`EventSource` can't attach custom headers. For production, use a same-origin
reverse proxy that injects `x-ecp-api-key` instead.

## Commands

```bash
npm run test          # vitest
npm run typecheck     # tsc --noEmit
npm run build         # outputs to dist/
```
