#!/usr/bin/env bash
# seed_remote.sh — reset a remote ECP deployment's demo data.
#
# Points the local Python scripts at the remote Neon + Aura databases by
# exporting ECP_POSTGRES_DSN and ECP_NEO4J_* in this shell, then runs
# init_db.py and seed_data.py. No network path to Render needed — we talk
# directly to Neon and Aura from your laptop.
#
# Usage:
#   # Option A: export the env vars in your shell, then run
#   export ECP_POSTGRES_DSN='postgresql://user:pass@host/db?sslmode=require'
#   export ECP_NEO4J_URI='neo4j+s://<id>.databases.neo4j.io'
#   export ECP_NEO4J_USER='neo4j'
#   export ECP_NEO4J_PASSWORD='...'
#   export ECP_VOYAGE_API_KEY='pa-...'     # optional; skip → ILIKE fallback
#   export ECP_EMBEDDING_PROVIDER=voyage   # optional; matches render.yaml
#   export ECP_EMBEDDING_DIM=512           # optional; matches render.yaml
#   ./scripts/seed_remote.sh
#
#   # Option B: put them in a local .env.remote (gitignored) and source it
#   set -a && . .env.remote && set +a && ./scripts/seed_remote.sh
#
# What this does (in order):
#   1. Validate required env vars are set (fail fast with a useful message).
#   2. Refuse to run against localhost / compose host (catches copy-paste mistakes).
#   3. Warn for 5s — this WIPES existing demo assets in Postgres and Neo4j.
#   4. python scripts/init_db.py    — idempotent schema (CREATE IF NOT EXISTS).
#   5. python scripts/seed_data.py  — TRUNCATE CASCADE + reload fixtures.
#
# This is how we reset demo state between sessions. Production databases
# MUST NOT be pointed at this script — it is destructive by design.
#
# Exit non-zero on any failure so CI / Render one-off jobs can gate on it.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

require() {
    local name="$1"
    if [[ -z "${!name:-}" ]]; then
        echo "ERROR: $name is not set. See the usage block at the top of $0." >&2
        exit 2
    fi
}

require ECP_POSTGRES_DSN
require ECP_NEO4J_URI
require ECP_NEO4J_USER
require ECP_NEO4J_PASSWORD

# Sanity: refuse to seed a DSN that looks local. Remote = has a host, is not
# 'localhost' or '127.0.0.1'. This catches the common copy-paste mistake of
# running seed_remote against a dev Docker stack.
case "$ECP_POSTGRES_DSN" in
    *@localhost*|*@127.0.0.1*|*@postgres:*)
        echo "ERROR: ECP_POSTGRES_DSN looks local. seed_remote.sh is for hosted databases." >&2
        echo "       Use 'python scripts/init_db.py && python scripts/seed_data.py' for local." >&2
        exit 2
        ;;
esac

echo "============================================================"
echo " seed_remote.sh — resetting demo data on REMOTE databases"
echo "============================================================"
echo " Postgres DSN host : $(echo "$ECP_POSTGRES_DSN" | sed -E 's|.*@([^/?]+).*|\1|')"
echo " Neo4j URI         : $ECP_NEO4J_URI"
echo " Embedding provider: ${ECP_EMBEDDING_PROVIDER:-voyage}"
echo " Embedding dim     : ${ECP_EMBEDDING_DIM:-512}"
echo "------------------------------------------------------------"
echo " This will TRUNCATE CASCADE the assets table and DETACH DELETE"
echo " every Neo4j node in the target instance. Ctrl-C within 5s to abort."
echo "============================================================"
sleep 5

echo "[1/2] Initializing schema (idempotent)…"
python scripts/init_db.py

echo "[2/2] Seeding fixtures…"
python scripts/seed_data.py

echo "------------------------------------------------------------"
echo "Done. Remote demo data loaded."
echo "Verify with:  curl -sH \"x-ecp-api-key: \$ECP_API_KEY\" \"\$ECP_BASE_URL/health\" | jq ."
