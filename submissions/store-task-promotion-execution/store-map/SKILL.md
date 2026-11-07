---
name: store-map
description: Retrieves one store's profile for the promotion readiness test — format, cluster, fixtures, received assets, completed tasks, prior execution history and current shelf prices — from the store master, receiving, task-system and POS exports into store.json + shelf-prices.json. Use after pack-ingest, or when the user asks "what does this store actually have", "pull the store profile for <id>", "what's been received at the store", "which launch tasks are done", "get the current shelf prices for store <id>". Do NOT use for floor plans, department layouts or wayfinding maps — use a store layout / planogram tool instead; not for the readiness verdict — use readiness-check instead; not for ingesting the HQ pack — use pack-ingest instead.
license: Proprietary
metadata: {version: "1.0.5", author: Microsoft Retail & CPG Skills, category: research, icon: DocumentTable}
---
# Store Map

## Purpose
Assemble the store side of the readiness equation: the profile plus what is physically confirmed on site, from records only. Mapping only — the readiness verdict belongs to the engine.

## When to use
After pack-ingest in every run, or whenever a store's confirmed state is needed for the readiness test.

## When NOT to Use
- A map of where departments sit, a floor plan or a wayfinding sign — use a store layout / planogram tool instead; this skill maps records, not space.
- The campaign pack or price-change file needs ingesting — use pack-ingest instead.
- "Are we ready" / "any gaps" — use readiness-check instead once store.json exists.
- Ranking the gaps or writing the brief — use exception-raise instead for the ranking, use brief-draft instead for the brief.

## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Files the user names, links or attaches in the chat.
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by campaign ID, store ID or file name when no location is given.
- Email attachments (for example a store manager's note) found the same way.

Read each source with the file reader (ReadFileContent) and cite it by file name and row or page. Write the working JSON files (`store.json`, `shelf-prices.json`) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values.

## Inputs
Store master export (format, cluster, fixtures); receiving confirmations; task-system export; current POS shelf-price extract, from the user's Microsoft 365 content (see *Where the data comes from*). Keep the export identity (export_id / ASN / row) as the citation.

## Steps
1. Build `store.json` from the exports (schema below): `store_id`, `format`, `cluster`, `fixtures[]`, `received_assets[]`, `completed_tasks[]`, plus `open_tasks[]` and `citations{}`.
2. Build `shelf-prices.json` from the POS extract: a flat `{ "<SKU>": <current shelf price> }` map — the exact shape `readiness_check.py --prices` reads.
3. Keep export identities as citations on every record; leave `prior_execution_history[]` empty with a note when no history export was supplied.
4. Validate the merged payload if you attach it to pack.json: `python tools/validate_contract.py payload.json`.

## Output format
Two files, shapes fixed so the engine can read them without translation:

```json
// store.json
{ "store_id": "ST-0781", "format": "small", "cluster": "suburban-standard",
  "fixtures": ["front-window"],
  "received_assets": ["SIGN-KIT-B", "POG-EC-19"],
  "completed_tasks": ["hang-front-banner"],
  "open_tasks": ["build-endcap", "hang-flags", "clip-strip"],
  "prior_execution_history": [],
  "as_of_date": "2026-08-15",
  "citations": { "profile": "STOREMASTER-2026-08-15-0781", "receiving": "RECV-2026-08-15-0781",
                 "tasks": "TASKSYS-2026-08-15-0781" } }
// shelf-prices.json
{ "GTIN-2001": 14.99, "GTIN-2002": 7.99, "GTIN-2003": 2.49, "GTIN-2004": 4.29 }
```
`format`, `cluster`, `fixtures`, `received_assets`, `completed_tasks` are flat string lists (as in the example above). Summarise to the user as a table: field | value | source export.

## Grounding requirements
Fixtures and confirmations come from records, never assumptions — "it always has an end-cap" is not a record. Every value names its export.

## Guardrails
- Never fill format, cluster or fixtures from what a store "normally" has; if the store master export is missing, leave them `null`, set `profile_status: "MISSING"` and ask store ops for the export — readiness is blocked (`references/execution-rules.md` #6).
- Never count an open task as done or an ASN as received without the confirmation row.
- Never include personal data (associate addresses, pay, schedules) — it is outside this contract; decline and point to HR/store ops.
- Do not compute applicability, completeness or price conflicts here; the verdict is the readiness_check engine's.
- Always show the mapped table for review before readiness-check runs.

## Escalation / uncertainty
Missing store profile → confidence below the floor, readiness blocked (#6): map what the other exports support and escalate for the profile. Conflicting exports (two formats for one store) → escalate to store ops; do not pick one.
