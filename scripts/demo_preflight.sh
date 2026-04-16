#!/usr/bin/env bash
#
# demo_preflight.sh — verify the Claude Desktop demo will resolve cleanly
# before you go live. Runs the Act I (finance analyst) and Act II (sales
# director) resolve calls via curl, asserts the right concept IDs came back,
# and exits non-zero if anything is off.
#
# Usage:
#   ./scripts/demo_preflight.sh                  # defaults: localhost:8080, no API key
#   ECP_BASE_URL=http://127.0.0.1:8080 \
#   ECP_API_KEY=sk-... \
#     ./scripts/demo_preflight.sh
#
# Exit codes:
#   0  all checks passed — safe to demo
#   1  /health unreachable or not ok
#   2  finance persona did not resolve to net_revenue + region_apac_finance
#   3  sales persona did not resolve to gross_revenue + region_apac_sales
#   4  finance and sales resolutions were identical (context not differentiating)
#   5  missing dependency (curl or jq)

set -o pipefail

BASE_URL="${ECP_BASE_URL:-http://127.0.0.1:8080}"
API_KEY="${ECP_API_KEY:-}"
CONCEPT="${ECP_PREFLIGHT_CONCEPT:-What was APAC revenue last quarter?}"

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

say()  { printf '%s\n' "$*"; }
ok()   { printf '  %s✓%s %s\n' "$GREEN" "$RESET" "$*"; }
warn() { printf '  %s!%s %s\n' "$YELLOW" "$RESET" "$*"; }
fail() { printf '  %s✗%s %s\n' "$RED" "$RESET" "$*"; }

for bin in curl jq; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    fail "required command not found: $bin"
    exit 5
  fi
done

auth_header=()
if [ -n "$API_KEY" ]; then
  auth_header=(-H "x-ecp-api-key: ${API_KEY}")
fi

say "${BOLD}ECP demo preflight${RESET}"
say "  base_url = ${BASE_URL}"
say "  concept  = ${CONCEPT}"
say ""

# ---------- 1. health ----------
say "${BOLD}1/4 health${RESET}"
health_body="$(curl -sS --max-time 5 "${auth_header[@]}" "${BASE_URL}/health" || true)"
if [ -z "$health_body" ]; then
  fail "no response from ${BASE_URL}/health — is the server up? (uvicorn src.main:app --port 8080)"
  exit 1
fi
status="$(printf '%s' "$health_body" | jq -r '.status // empty')"
mode="$(printf '%s' "$health_body" | jq -r '.mode // empty')"
if [ "$status" != "ok" ]; then
  fail "/health returned status=${status:-<missing>}: $health_body"
  exit 1
fi
ok "server ok (resolution mode: ${mode:-unknown})"
say ""

# ---------- 2. finance persona ----------
say "${BOLD}2/4 finance analyst resolve${RESET}"
finance_body="$(curl -sS --max-time 15 \
  -X POST "${BASE_URL}/api/v1/resolve" \
  -H 'Content-Type: application/json' \
  -H 'x-ecp-user-id: demo_finance_analyst' \
  -H 'x-ecp-department: finance' \
  -H 'x-ecp-role: analyst' \
  "${auth_header[@]}" \
  --data "$(jq -n --arg c "$CONCEPT" '{concept:$c, user_context:null}')" || true)"

if [ -z "$finance_body" ]; then
  fail "no response from /api/v1/resolve (finance)"
  exit 2
fi

finance_metric="$(printf '%s' "$finance_body" | jq -r '.resolved_concepts.metric.resolved_id // empty')"
finance_dim="$(printf '%s' "$finance_body" | jq -r '.resolved_concepts.dimension.resolved_id // empty')"
finance_quarter="$(printf '%s' "$finance_body" | jq -r '.execution_plan[0].parameters.filters.date_range.label // empty')"
finance_conf="$(printf '%s' "$finance_body" | jq -r '.confidence.overall // empty')"
finance_warnings="$(printf '%s' "$finance_body" | jq -r '[.warnings[]?.id] | join(",")')"
finance_resolution_id="$(printf '%s' "$finance_body" | jq -r '.resolution_id // empty')"

printf '    metric      = %s\n' "${finance_metric:-<none>}"
printf '    dimension   = %s\n' "${finance_dim:-<none>}"
printf '    quarter     = %s\n' "${finance_quarter:-<none>}"
printf '    confidence  = %s\n' "${finance_conf:-<none>}"
printf '    warnings    = %s\n' "${finance_warnings:-<none>}"

if [ "$finance_metric" != "net_revenue" ]; then
  fail "expected metric=net_revenue, got '${finance_metric}'"
  say ""
  say "full response:"
  printf '%s\n' "$finance_body" | jq . >&2 || printf '%s\n' "$finance_body" >&2
  exit 2
fi
if [ "$finance_dim" != "region_apac_finance" ]; then
  fail "expected dimension=region_apac_finance, got '${finance_dim}'"
  exit 2
fi
ok "finance resolves to net_revenue + region_apac_finance (resolution_id=${finance_resolution_id})"
say ""

# ---------- 3. sales persona ----------
say "${BOLD}3/4 sales director resolve${RESET}"
sales_body="$(curl -sS --max-time 15 \
  -X POST "${BASE_URL}/api/v1/resolve" \
  -H 'Content-Type: application/json' \
  -H 'x-ecp-user-id: demo_sales_director' \
  -H 'x-ecp-department: sales' \
  -H 'x-ecp-role: director' \
  "${auth_header[@]}" \
  --data "$(jq -n --arg c "$CONCEPT" '{concept:$c, user_context:null}')" || true)"

if [ -z "$sales_body" ]; then
  fail "no response from /api/v1/resolve (sales)"
  exit 3
fi

sales_metric="$(printf '%s' "$sales_body" | jq -r '.resolved_concepts.metric.resolved_id // empty')"
sales_dim="$(printf '%s' "$sales_body" | jq -r '.resolved_concepts.dimension.resolved_id // empty')"
sales_quarter="$(printf '%s' "$sales_body" | jq -r '.execution_plan[0].parameters.filters.date_range.label // empty')"
sales_conf="$(printf '%s' "$sales_body" | jq -r '.confidence.overall // empty')"
sales_warnings="$(printf '%s' "$sales_body" | jq -r '[.warnings[]?.id] | join(",")')"
sales_resolution_id="$(printf '%s' "$sales_body" | jq -r '.resolution_id // empty')"

printf '    metric      = %s\n' "${sales_metric:-<none>}"
printf '    dimension   = %s\n' "${sales_dim:-<none>}"
printf '    quarter     = %s\n' "${sales_quarter:-<none>}"
printf '    confidence  = %s\n' "${sales_conf:-<none>}"
printf '    warnings    = %s\n' "${sales_warnings:-<none>}"

if [ "$sales_metric" != "gross_revenue" ]; then
  fail "expected metric=gross_revenue, got '${sales_metric}'"
  say ""
  say "full response:"
  printf '%s\n' "$sales_body" | jq . >&2 || printf '%s\n' "$sales_body" >&2
  exit 3
fi
if [ "$sales_dim" != "region_apac_sales" ]; then
  fail "expected dimension=region_apac_sales, got '${sales_dim}'"
  exit 3
fi
ok "sales resolves to gross_revenue + region_apac_sales (resolution_id=${sales_resolution_id})"
say ""

# ---------- 4. persona differentiation ----------
say "${BOLD}4/4 personas differ${RESET}"
if [ "$finance_metric" = "$sales_metric" ] && [ "$finance_dim" = "$sales_dim" ]; then
  fail "finance and sales resolved identically — department context is not differentiating"
  exit 4
fi
ok "finance and sales resolved differently — context is the product"

# quarter sanity: should be the same label for both (same wall clock), but surface it
if [ -n "$finance_quarter" ] && [ "$finance_quarter" != "$sales_quarter" ]; then
  warn "finance quarter='$finance_quarter' but sales quarter='$sales_quarter' — unexpected, fiscal calendar should be user-independent"
fi

say ""
say "${BOLD}preflight OK${RESET} — demo is ready."
say "  finance resolution_id: ${finance_resolution_id}"
say "  sales   resolution_id: ${sales_resolution_id}"
say "  fiscal quarter label:  ${finance_quarter:-<none>}"
exit 0
