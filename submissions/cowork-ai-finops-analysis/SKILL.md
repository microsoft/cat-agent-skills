---
name: cowork-ai-finops-analysis
description: Builds the "AI FinOps Admin Console" — a single, self-contained, app-like HTML file (11 segments, period selector, sortable tables, charts) showing the CURRENT tenant's AI spend and consumption — from three plugins - A365 Analytics (Viva Insights), Microsoft 365 Admin Center and Power Platform Admin. Use when an admin asks for an "AI FinOps console/report/snapshot as HTML", "FinOps dashboard file", "AI spend report for my tenant", or "Copilot / agents / Cowork / credits / spending policies overview I can share". Not for a live Managed App, Word/PowerPoint reports or a single quick metric answered in chat.
---

# AI FinOps Admin Console (HTML snapshot)

Produces `ai-finops-admin-console-<tenant>-<yyyy-mm-dd>.html` in `output/`: the full console UI with the
tenant's data embedded (works offline, no sign-in, ~3–4 MB). The user sees an app with these segments:
Overview · Spend & forecast · Credits & billing · Spending policies · Users · Agents · Cowork ·
Microsoft 365 Copilot · Power Platform · Tenant & security · Data catalog, and a 7 days / 30 days /
Quarter to date / 90 days period selector.

## Bundled files (paths relative to this skill's folder)

| File | Purpose |
|---|---|
| `assets/console-template.html` | Compiled console UI with a `__FINOPS_DATA__` placeholder. Never edit by hand. |
| `scripts/capture.py` | Data capture, run with `core-RunScript`, one `part` per run. |
| `scripts/build.py` | Merges captured data into the template → final HTML. Plain Python (Bash). |

## Prerequisites (check, do not assume)

The user must be a Global Admin / AI Admin / Billing reader in the tenant, and these must be enabled for the task:
1. **A365 Analytics** (Viva Insights MCP, tools `vivainsightsmcp-*`).
2. **Microsoft 365 Admin Center** MCP (tools such as `<server>-GetCopilotCreditsSummary`).
3. **Power Platform Admin** (connector `shared_powerplatformadminv2` via `powerplatform-*` tools).

If one is missing, say which one and continue with the others. Some unavailable
reports show "Not in this snapshot", but other views can display zero or empty
values when data is missing. Never treat these as verified measurements.

## Workflow

Track these steps with the task tools. Describe progress in business words only.

### 1. Resolve the four run parameters

- **today** — the user's local date (`YYYY-MM-DD`) from the system context.
- **admin_server** — `tool_search_tool` with pattern `GetCopilotCreditsSummary`. The tool name is
  `<prefix>-GetCopilotCreditsSummary`; `admin_server` is that `<prefix>` (often a GUID). If not found, the
  admin center plugin is missing — set `admin_server` to `"none"` and skip the `admin_*` parts.
- **act_as** (Viva Insights perspective) — if A365 Analytics is available, call `vivainsightsmcp-whoami` (or any Viva tool without `actAs`);
  it lists perspectives as `self:<partitionId>:<role>`. Prefer the **Global partition** with the broadest
  role, in this order: `Chief_Officer` → `Nova_Business_Decision_Maker` → `Nova_Analyst`. If no Global
  partition exists and several remain, ask the user once with `core-AskUserQuestion`.
- **pp_connection_id** — if Power Platform Admin is available, call `powerplatform-ListConnections` filtered to connector
  `shared_powerplatformadminv2`; use a connected one. If none exists, ask the user to authorize creating one with
  `powerplatform-CreateConnection` (the user signs in), then use its id. Skip Power Platform if unavailable or declined.
- **tenant** (display only) — the organization name from `me_profile-GetMyDetails` (company), else the tenant domain.

### 2. Stage the capture script

Copy `scripts/capture.py` from this skill into the workspace as `.aether/scripts/finops_capture.py`
(one Bash call: `mkdir -p .aether/scripts && cp <skill>/scripts/capture.py .aether/scripts/finops_capture.py`).
Create a fresh snapshot directory for every new run using `mkdir -p working && mktemp -d working/finops-snap.XXXXXX`.
Record the returned path as `<snap>` and use it for all parts and the build. When continuing an interrupted run,
reuse that run's `<snap>`; never reuse it for a new snapshot, tenant, or different source selection.

### 3. Capture data — one `core-RunScript` call per part

Call `core-RunScript` with `path: ".aether/scripts/finops_capture.py"` and
`args: {"part": "<part>", "today": "...", "admin_server": "...", "act_as": "...", "pp_connection_id": "...", "out_dir": "<snap>"}`.

Independent parts may run in parallel (same batch). Order constraints:

| Batch | Parts | Notes |
|---|---|---|
| A (parallel) | `admin_base`, `admin_periods`, `viva_7`, `viva_30`, `viva_qtd`, `viva_90`, `viva_fixed`, `pp_base` | ~10–45 s each |
| B (parallel) | `admin_trends` (needs `admin_periods`), `pp_envs` with `env_offset: 0` (needs `pp_base`) | |
| C (loop) | `pp_envs` with `env_offset` = previous result's `next_env_offset` | repeat until `next_env_offset` is null; 50 environments per run keeps each run under 5 minutes |
| D | `retry` with `limit: 40` | re-reads throttled/transient failures; run at most twice |

Skip `admin_*` parts when `admin_server` is `"none"`, `viva_*` when Viva is unavailable, `pp_*` when there is no
Power Platform connection. Report per-part errors only as a summary; 404s on some Copilot Credits reports
(PAYG overview, policy health, model/environment/policy/resource consumption, service trends) are normal —
Microsoft doesn't provide those reports for every tenant yet.
The retry limit is shared across both sources; each attempted read is checkpointed. Retry stops starting new
reads after four minutes, but an individual connector call can still take longer. Report remaining or failed
reads and any `catalog_error` from `viva_fixed` as unavailable data.

### 4. Build, check, publish

One Bash call:

```
python3 <skill>/scripts/build.py --snap <snap> \
  --template <skill>/assets/console-template.html \
  --out working/ai-finops-admin-console-<tenant-slug>-<today>.html --today <today> --tenant "<tenant>"
```

Then, when available, check it with the html skill validator (`validate.py` must report `success`), and publish with
`host-CopyArtifact(surface="output", source="working/<file>.html", destination="<file>.html")`; confirm `"ok": true`.

### 5. Report to the user

Name the file exactly. Summarize in 4–6 bullets: top-line AI spend for the quarter (USD, Viva Insights),
credits consumed (admin center), active Copilot users, number of agents, spending policies, and which data
sources were unavailable. Remind them:
- It is a point-in-time snapshot (date shown in the header); re-run the skill to refresh.
- The file contains tenant data (user names, costs) — share only with authorized people.
- Some unavailable or failed reports can display zero or empty values, including AI spend and forecasts;
  verify the source data before relying on them. Do not report those values as measured when the source failed.
- Admin-center credits and Viva Insights credits use different definitions; never add credits to USD.
- Viva Insights data lags about a week and hides groups below the privacy minimum.

## Rules

- Never edit `assets/console-template.html`; all tenant data goes in through `build.py`.
- Do not put tenant data in chat beyond the short summary.
- Do not run write/update tools from any of the three plugins; this skill is read-only.
- Creating a Power Platform connection requires the user's approval; it does not change tenant settings.
- Each RunScript run must finish in under 5 minutes; keep `pp_envs` batches at 50 or fewer environments.
