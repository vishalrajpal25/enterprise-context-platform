# Demo Screenshots

Drop dry-run screenshots here. The filenames below are the ones the runbook
and any follow-up blog/slide materials will reference, so stick to them.

Do **not** commit raw screen captures that include API keys, machine
hostnames, or internal Slack handles. Crop or blur before committing.

## What to capture during a dry-run

Run through [../DEMO-RUNBOOK.md](../DEMO-RUNBOOK.md) once end-to-end before
the live demo. At each of these moments, capture the image.

| # | Filename                          | Moment                                                                                                    | What the image should show                                                                                                                                          |
| - | --------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | `01-preflight-ok.png`             | After `./scripts/demo_preflight.sh` exits 0.                                                              | The full terminal output: health OK, finance resolve OK, sales resolve OK, "personas differ" OK, final `preflight OK` line with both resolution_ids and the fiscal quarter. |
| 2 | `02-claude-desktop-toolsets.png`  | In Claude Desktop, tools picker open in a fresh chat after restart.                                       | Both `ecp-finance-analyst` and `ecp-sales-director` visible in the connected-tools list, each showing 5 tools.                                                       |
| 3 | `03-act1-finance-resolution.png`  | Act I, after Claude calls `resolve_concept` with the finance toolset.                                     | Claude's tool-use panel expanded, showing the JSON response: `metric.resolved_id = "net_revenue"`, `dimension.resolved_id = "region_apac_finance"`, 3 warnings listed, confidence ~0.90. |
| 4 | `04-act1-provenance.png`          | Act I, `get_provenance` response.                                                                         | The full session payload — parsed_intent, resolution_dag with 6 steps (parse_intent → authorize), execution_plan, feedback_status "pending", owner `demo_finance_analyst`.          |
| 5 | `05-act1-feedback-accepted.png`   | Act I, `report_feedback` response.                                                                        | `{"status": "recorded", "resolution_id": "rs_..."}` in Claude's tool panel.                                                                                         |
| 6 | `06-act2-sales-resolution.png`    | Act II, after `resolve_concept` is called with the sales toolset on the **same** question.               | Same JSON view as #3 but now `metric = "gross_revenue"`, `dimension = "region_apac_sales"`, 2 warnings (cost-center warning gone), country list visibly shorter (excludes AU/NZ). |
| 7 | `07-act2-side-by-side.png`        | Terminal or split-screen view showing Act I vs Act II response side by side.                              | The diff moment: same `concept`, same `fiscal_quarter.label = "Q4-FY2026"`, different `metric` + `dimension` + warnings. This is the money shot for slides.         |
| 8 | `08-act3-precedent-or-noboost.png`| Act III, repeat finance resolve.                                                                          | Either (a) `precedents_used` populated with the Act I resolution_id and "CONFIDENCE_BOOST" influence — if an embedding key is set — or (b) empty `precedents_used` + `get_provenance` on the Act I id showing `feedback_status: "accepted"`. Whichever one you actually demo. |
| 9 | `09-recovery-403-other-persona.png` | Optional. Call `get_provenance` for the Act I resolution_id from the sales toolset.                      | The 403 Forbidden response body: `{"detail": "Forbidden: resolution does not belong to caller"}`. Good for the governance beat.                                     |

## Style notes

- Use a solid, neutral wallpaper (no personal photos) while capturing.
- Dark mode is fine and is what most audiences expect for terminal shots;
  light mode is better for Claude Desktop since its UI is light.
- Keep the Claude Desktop window at a normal reading width (~900 px);
  ultra-wide captures are hard to read in slide decks.
- If you capture the terminal, leave the final prompt visible — that hints
  to the viewer that it's a live run, not a mockup.

## What NOT to capture

- Any response body that includes `ECP_API_KEY`, bearer tokens, or real
  user emails from the seed data should be cropped. The demo seed has
  emails like `sarah.johnson@company.com` that are clearly placeholder —
  those are fine — but scrub anything that looks like a real account.
- The Claude Desktop settings page (shows your Anthropic account email).
- Desktop notifications, calendar events, or other chrome.
