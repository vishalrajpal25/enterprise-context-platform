# ECP x Claude Desktop — Demo Runbook

A five-minute, prompt-by-prompt demo that shows the same question getting two
different correct answers in Claude Desktop, because ECP resolves meaning
before computation.

> Looking for the browser-UI runbook? See [DEMO-RUNBOOK-studio-ui.md](DEMO-RUNBOOK-studio-ui.md).

---

## What the audience will see

One question — `"What was APAC revenue last quarter?"` — asked twice inside
Claude Desktop, once as a **finance analyst** and once as a **sales director**.

| Persona          | Metric          | Region dimension                     | Tribal warnings                                              |
| ---------------- | --------------- | ------------------------------------ | ------------------------------------------------------------ |
| finance analyst  | `net_revenue`   | `region_apac_finance` (includes ANZ) | Q4-2019 APAC gap · APAC cost-center change 2021 · FX gotcha  |
| sales director   | `gross_revenue` | `region_apac_sales` (excludes ANZ)   | Q4-2019 APAC gap · FX gotcha                                 |

Both get the same fiscal quarter (computed live from wall clock), both get a
confidence of ~0.90, both record a decision trace. The punchline: **same
question, same data, different correct answers — because context is the
product.**

---

## Pre-flight (~30 s of your time; stack warms up in ~45 s)

From the repo root:

```bash
# 1. Start infra (Neo4j, Postgres+pgvector, Redis)
docker compose up -d

# 2. Init schema + seed the financial-data-company scenario
python scripts/init_db.py
python scripts/seed_data.py

# 3. Boot the API. ECP_OPA_DEFAULT_ALLOW=true is required for the demo —
#    without OPA running and without this flag, the fail-closed default
#    filters every concept out of the response.
ECP_OPA_DEFAULT_ALLOW=true uvicorn src.main:app --port 8080

# 4. In a second terminal: confirm it's up
curl -s http://127.0.0.1:8080/health | jq .
# -> {"status":"ok","mode":"orchestrator","demo_mode":false,"version":"3.0.0",...}

# 5. Verify both personas resolve cleanly BEFORE going live
./scripts/demo_preflight.sh
# -> preflight OK — demo is ready.
```

If `demo_preflight.sh` prints green checks for all four sections, you are
safe to demo. It exercises the exact same HTTP path Claude Desktop will use
(resolve with identity headers).

---

## Claude Desktop setup (~60 s, one-time)

1. Copy [claude_desktop_config.example.json](claude_desktop_config.example.json)
   to the Claude Desktop config location:

   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   ```bash
   # macOS one-liner (from repo root)
   mkdir -p ~/Library/Application\ Support/Claude
   cp docs/demo/claude_desktop_config.example.json \
      ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Edit the copy. Replace every `ABSOLUTE_PATH_TO_REPO` with the real
   absolute path (e.g.
   `/Users/you/Documents/projects/enterprise-context-platform`). Leave
   `ECP_API_KEY` empty unless you've set `ECP_API_KEY` on the server.
   Leave `ECP_BASE_URL` as `http://127.0.0.1:8080` for the local demo, or
   point it at your hosted instance.

3. **Fully quit** Claude Desktop (`Cmd+Q` on macOS — closing the window is
   not enough; Claude Desktop only re-reads its MCP config on a full
   restart) and relaunch it.

4. Start a new chat. Click the tools icon (hammer / plug / wrench icon
   depending on version). You should see two toolsets listed:

   - **ecp-finance-analyst** — 5 tools (resolve_concept, execute_metric, report_feedback, search_context, get_provenance)
   - **ecp-sales-director** — same 5 tools

   Each toolset is the *same* MCP server pointed at the *same* ECP instance
   — they differ only in the identity headers baked into the server's env.

---

## Act I — Finance analyst (~90 s)

Tell Claude:

> **Using the ecp-finance-analyst tools, resolve "What was APAC revenue last
> quarter?"**

Expected tool call: `resolve_concept(concept="What was APAC revenue last quarter?")`.

Expected resolution:

| Field              | Value                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------ |
| metric             | `net_revenue` → `cube.finance.Revenue.netRevenue`                                          |
| region dimension   | `region_apac_finance` (9 countries, includes AU + NZ)                                      |
| fiscal time        | `Q4-FY2026` = 2026-01-01 → 2026-03-31 (fiscal year starts April; today is 2026-04-16, so "last quarter" is the quarter that just closed, Jan–Mar) |
| confidence overall | ~0.90 (definition 1.0 · data_quality 0.7 · temporal_validity 1.0 · authorization 1.0 · completeness 0.9) |
| tribal warnings    | 3 — `tk_apac_q4_2019`, `tk_apac_costcenter_2021`, `tk_fx_rates`                            |
| resolution_id      | `rs_<yyyymmdd>_<hex>` — save this for provenance and feedback                              |

Narrator beats:
- *"Notice the warnings — the system knows Q4 2019 APAC data is incomplete
  and that cost centers changed in 2021. Nobody told Claude. That's tribal
  knowledge captured in ECP and attached to the resolution."*
- *"The time resolver computed Q4-FY2026 from today's wall clock against the
  fiscal calendar config — it's not a hardcoded demo string."*

Then:

> **Get the provenance for that resolution.**

Expected: `get_provenance(resolution_id=…)` returns the full session —
`original_query`, `parsed_intent`, `resolution_dag` (6 steps: parse_intent
→ resolve_metric → resolve_dimension → resolve_time → check_tribal_knowledge
→ authorize), `execution_plan`, `confidence`, `feedback_status: "pending"`,
owner `demo_finance_analyst`.

Narrator: *"Every resolution leaves an audit trail. Try to fetch it as the
sales director and you'll get 403 — resolutions are owner-bound."*

Then:

> **Report that resolution as accepted.**

Expected: `report_feedback(resolution_id=…, feedback="accepted")` returns
`{"status": "recorded", "resolution_id": "…"}`. The session's
`feedback_status` flips to `"accepted"` in Postgres — visible via a second
`get_provenance` call if the audience wants proof.

---

## Act II — Sales director (~90 s)

In the **same** Claude Desktop chat, tell Claude:

> **Now use the ecp-sales-director tools. Same question: "What was APAC
> revenue last quarter?"**

Expected: a tool call that resolves identically in surface form — same
concept, same fiscal quarter — but with a materially different answer.

| Field              | Value                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------ |
| metric             | `gross_revenue` → `cube.finance.Revenue.grossRevenue` (tier 2, not tier 1)                 |
| region dimension   | `region_apac_sales` (7 countries, **excludes AU + NZ** — ANZ books separately in sales)    |
| fiscal time        | `Q4-FY2026` = 2026-01-01 → 2026-03-31 (same — fiscal calendar is user-independent)         |
| confidence overall | ~0.90 (same formula; tier-2 metric does not mean lower confidence here)                    |
| tribal warnings    | 2 — `tk_apac_q4_2019`, `tk_fx_rates` (the cost-center warning does **not** fire: in Neo4j it's attached to `net_revenue`, not `gross_revenue`) |

**The punchline for the room.** Same prompt, same data, different:
- definition of revenue (gross vs net — ASC 606 vs invoiced)
- country set behind "APAC" (ANZ in vs out)
- certification tier (1 vs 2)
- tribal warnings surfaced

All three came from the *same* registry, resolved by ECP based on the
identity headers the MCP server injected. Claude Desktop never touched the
graph, never wrote SQL, never guessed. It asked ECP for meaning, got a
deterministic execution plan back, and that plan would run against the
semantic layer.

Narrator:
- *"If both teams wired up Claude Desktop to the warehouse directly, they'd
  either fight over definitions or build the same dashboards twice. ECP is
  the semantic firewall."*
- *"This is the math-vs-meaning point from the spec: the semantic layer
  does math, ECP picks which math."*

---

## Act III — Precedent learning (~60 s)

Go back to the finance analyst toolset:

> **Using the ecp-finance-analyst tools, resolve "What was APAC revenue
> last quarter?" again.**

What to expect **depends on whether embeddings are configured**:

- **With an embedding key set (`ECP_VOYAGE_API_KEY` or `ECP_OPENAI_API_KEY`):**
  The precedent engine does cosine search over past query embeddings. The
  accepted Act I resolution comes back as a precedent with
  `feedback: "accepted"` and
  `influence: "CONFIDENCE_BOOST: Similar query (sim=0.9x) resolved and accepted."`
  The overall confidence nudges up.

- **Without an embedding key (the default for this demo — you'll see
  `"embedding_available": false` in `/health`):** the precedent engine
  falls back to ILIKE on concept tokens. It does not match natural
  phrasing like *"What was APAC revenue last quarter?"* against the
  stored concept-token string `"revenue apac last_quarter"`, so the
  precedents list comes back empty and confidence is unchanged. The
  feedback still persists — prove it by calling `get_provenance` on the
  Act I resolution_id and showing `feedback_status: "accepted"`.

Frame it honestly: *"The feedback loop is end-to-end persisted — the
precedent retrieval quality is a function of the embedding provider you
wire up."*

> If precedent-correction-propagation from Session C has shipped and the
> fiscal-date precedent override is live, replace Act III with the
> correction scenario: report the first resolution as `corrected` with a
> `correction_details` like *"use net revenue per GAAP, not ASC 606"*,
> then re-ask the same question and highlight the
> `HARD_CONSTRAINT: Previous resolution was corrected` precedent
> influence.

---

## Recovery

### "Claude Desktop doesn't show the ECP toolsets."

1. Did you fully quit Claude Desktop? (`Cmd+Q`, not just close the window.)
2. Is the JSON valid? `jq . ~/Library/Application\ Support/Claude/claude_desktop_config.json` should parse without error.
3. Did you replace `ABSOLUTE_PATH_TO_REPO` in **both** entries? Relative
   paths won't work.
4. Is `node` on the PATH Claude Desktop sees? Claude Desktop inherits a
   minimal PATH. If node is Homebrew's at `/opt/homebrew/bin/node`, put
   that absolute path in the config's `"command"` field instead of
   `"node"`.
5. Claude Desktop writes MCP logs to
   `~/Library/Logs/Claude/mcp-server-ecp-finance-analyst.log` and
   `~/Library/Logs/Claude/mcp-server-ecp-sales-director.log`. `tail -f`
   them while restarting — connection errors show up there.

### "The tool call returns but resolved_concepts is empty."

You forgot `ECP_OPA_DEFAULT_ALLOW=true` when starting uvicorn. Restart the
server with that env var set and re-run `./scripts/demo_preflight.sh`.
With OPA unreachable and the flag unset, the fail-closed default strips
every concept out of the response — correct for production, wrong for a
demo.

### "`/health` fails or curl can't connect."

- `docker compose ps` — are neo4j, postgres, redis all `running`?
- `docker compose logs neo4j --tail=50` — Neo4j 5 takes ~20 s to accept
  connections on first boot; the API will log `neo4j: connect failed`
  until it's ready.
- Port conflict: `lsof -i :8080`. If something else holds 8080, kill it
  or start uvicorn with `--port 8081` and set `ECP_BASE_URL` accordingly
  in both MCP config entries.

### "Docker is missing a service."

The compose file only defines three services: `neo4j`, `postgres`,
`redis`. If any failed to come up:

```bash
docker compose down
docker compose pull
docker compose up -d
docker compose ps
```

If postgres is `unhealthy` — most often disk space or a stale named volume
— `docker compose down -v` (destroys data; you'll re-seed), then
`docker compose up -d`, then re-run
`python scripts/init_db.py && python scripts/seed_data.py`.

### "I don't have `jq`."

Preflight needs `jq` and `curl`. `brew install jq` on macOS.

---

## Checklist (peel off while setting up)

- [ ] `docker compose up -d` — all three containers running
- [ ] `python scripts/init_db.py && python scripts/seed_data.py` — 28 assets, 42 Neo4j nodes
- [ ] `ECP_OPA_DEFAULT_ALLOW=true uvicorn src.main:app --port 8080` — server up
- [ ] `./scripts/demo_preflight.sh` — exits 0, both personas resolve differently
- [ ] `claude_desktop_config.json` copied to `~/Library/Application Support/Claude/`
- [ ] `ABSOLUTE_PATH_TO_REPO` replaced in both entries
- [ ] Claude Desktop fully quit and relaunched
- [ ] Both toolsets visible in the tools picker
