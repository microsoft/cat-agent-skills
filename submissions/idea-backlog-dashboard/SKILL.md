---
name: idea-backlog-dashboard
description: Self-contained package that builds an Idea Backlog solution - Dataverse Idea table, a Copilot Studio agent that captures ideas from users, and a Power Apps canvas dashboard showing ideas by status (New / In Progress / Completed) with a clickable detail view. Use when asked to create an idea/backlog/suggestion dashboard, idea capture agent, or idea tracker on Power Platform. Works in any environment/repo; no dependency on other projects.
---

# Idea Backlog Dashboard (portable skill)

End-to-end flow: **User -> Copilot Studio agent -> Dataverse `<prefix>_idea` -> Power Apps dashboard**.

## Inputs (ask only if not already known)
Environment variables (never print or commit values):
`DATAVERSE_ENV_URL`, `DATAVERSE_TENANT_ID`, `DATAVERSE_CLIENT_ID`, `DATAVERSE_CLIENT_SECRET` (service principal), `DATAVERSE_PUBLISHER_PREFIX` (existing publisher's prefix). Optional: solution unique name (default `IdeaBacklog`).

## Package contents (all relative to this folder)
| Path | Purpose |
| --- | --- |
| `scripts/Install-IdeaSchema.ps1` | Idempotently creates solution, `<prefix>_idea` table, columns, Status/Priority/Category choices via Dataverse Web API |
| `scripts/Import-Ideas.ps1` | Stores ideas (JSON from agent export/transcript or sample) into Dataverse |
| `scripts/Common.ps1` | Auth (client credentials) + REST helpers |
| `assets/sample-ideas.json` | Seed data |
| `references/data-model.md` | Table/column/choice definitions |
| `references/copilot-studio-agent.md` | Agent instructions, topic, Dataverse tool setup |
| `references/power-app.md` | Canvas app spec and Power Fx for dashboard, gallery, detail screen |
| `assets/IdeaBacklog.pa.yaml` | Reference canvas app source (replace `PREFIX` with the real prefix) |

## Procedure
1. **Connect/verify**: confirm env vars; if missing, stop and report variable names only. Load `dv-connect`/`dv-overview` skills if present for diagnostics.
2. **Schema**: `pwsh scripts/Install-IdeaSchema.ps1 [-SolutionName IdeaBacklog]`. Read back the table via `EntityDefinitions(LogicalName='<prefix>_idea')` to verify columns.
3. **Seed (optional)**: `pwsh scripts/Import-Ideas.ps1 -Path assets/sample-ideas.json`.
4. **Copilot Studio agent**: follow `references/copilot-studio-agent.md` (create agent, paste instructions, add Dataverse "Add a new row" tool on `Ideas`, publish). Agent writes directly to Dataverse; use `Import-Ideas.ps1` for any ideas captured elsewhere (JSON).
5. **Power App**: follow `references/power-app.md`. If the `canvas-apps-canvas-app` skill/Canvas Authoring MCP is available, use it with `assets/IdeaBacklog.pa.yaml` as the baseline; otherwise create the app in Studio and paste screen formulas. Add the `Ideas` table as data source, save, publish, add app to the solution.
6. **Validate**: new idea via agent appears in app after Refresh; filtering by status works; selecting a card opens detail screen; status change in detail persists.
7. **Share**: grant users the *Basic User* role plus Create/Read/Write on `Idea` (or a custom role), and share the app and agent.

## Rules
- Use the configured publisher prefix; do not invent one. Add all components to the solution; export with `pac solution export` when done.
- Status values: 100000000 New, 100000001 In Progress, 100000002 Completed. Keep them aligned across agent, app, scripts.
- Never store secrets in files.
