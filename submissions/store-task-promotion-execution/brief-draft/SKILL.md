---
name: brief-draft
description: Drafts the store readiness checklist, the shift brief in store language, and the exception escalation for a promotion launch from the ranked contract payload — draft-first, nothing sent. Use to close every execution run — "draft the shift brief", "write up the readiness pack", "build the launch checklist for store <id>", "what does the team do each shift", "write the escalation for the district manager". Do NOT use for field-sales store visit reports or action registers — use visit-report instead; not for the readiness test or ranking — use readiness-check instead for the test, use exception-raise instead for the ranking; not for ingesting the pack or store records — use pack-ingest instead for the pack, use store-map instead for the store records.
license: Proprietary
metadata: {version: "1.0.5", author: Microsoft Retail & CPG Skills, category: writing, icon: Compose}
---
# Brief Draft

## Purpose
Terminal artifacts — readiness checklist + shift brief + exception escalation — populated only from the contract payload (`ranked.json`). The store manager owns execution; this skill drafts.

## When to use
End of every execution run, once `ranked.json` exists.

## When NOT to Use
- A sales rep's store-visit write-up, audit photos, perfect-store action register — use visit-report instead.
- "Are we ready" or "what do we fix first" — use readiness-check instead for the test, use exception-raise instead for the ranking; this skill does not compute.
- The pack or store records are not assembled yet — use pack-ingest instead for the pack, use store-map instead for the store records.
- Anything that changes POS prices, planograms, labour schedules or campaign funding — out of the plugin boundary; draft the escalation, do not act.

## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Files the user names, links or attaches in the chat.
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by campaign ID, store ID or file name when no location is given.
- Email attachments (for example a store manager's note) found the same way.

Read each source with the file reader (ReadFileContent) and cite it by file name and row or page. Write the working JSON files (`READINESS-<campaign_id>-<store_id>.md`, `SHIFT-BRIEF-<campaign_id>-<store_id>.md`) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values.

## Inputs
`ranked.json` (full payload, from exception-raise or supplied by the user from their Microsoft 365 content, see *Where the data comes from*). Rules: `references/execution-rules.md`.

## Steps
1. Validate with the contract validator tool: `python tools/validate_contract.py ranked.json`. Price conflicts and fixture conflicts lead every artifact.
2. Checklist: per-requirement status with citations, completeness % verbatim. Shift brief: what each daypart does, in store language. Exceptions: the ranked list with revenue at stake for the district manager.
3. Mark every artifact DRAFT — the store manager reviews before anything is shared.

```markdown
# DRAFT — Shift Brief: <campaign>, Store <id>   (completeness 25.0% — NOT READY)
## The one thing everyone must know
Do NOT change the shelf price on GTIN-2002 — promo 8.99 ≥ shelf 7.99 (#3.1). HQ resolves.
## Sunday — day shift
- Front banner is up (SIGN-KIT-B, pack p.2) ...
```

## Output format
Two markdown files, named exactly:
- `READINESS-<campaign_id>-<store_id>.md` — checklist: sections *Conflicts first*, *Checklist* (table: req_id | status | detail | citation), *Price integrity*, *Exceptions for the district manager* (table in engine order with revenue at stake), *Boundary note*.
- `SHIFT-BRIEF-<campaign_id>-<store_id>.md` — brief: *The one thing everyone must know*, one section per daypart, *Manager only* escalation list.
Both start with `# DRAFT`.

## Grounding requirements
Every line cites pack, price file or store record; numbers come from the payload only.

## Guardrails
- Draft-first: never send, post or email the brief to the team, the district manager or anyone — show the draft and let the store manager decide; confirm before any distribution.
- A completeness % never rounds up; conflicts never disappear from the brief, however inconvenient.
- Any price conflict = an explicit "do not change the shelf" instruction in the brief until HQ resolves it.
- Never fabricate shelf prices, revenue or statuses missing from the payload — write "not in payload" instead.
- Nothing here changes POS prices, planograms, schedules or funding (plugin boundary).

## Escalation / uncertainty
If `ranked.json` fails validation or `readiness.blocked` is true (#6), draft a BLOCKED brief that names the missing input and stops — no checklist statuses are invented to fill it.
