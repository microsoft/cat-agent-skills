---
name: exception-raise
description: Ranks a store's promotion-launch readiness exceptions — missing kits, fixture conflicts, price conflicts from checked.json — by weekly revenue at stake with the exception_rank engine, and raises the exception list for the store and district manager. Use after readiness-check, or when the user asks "what do we fix first for the launch", "rank the readiness exceptions", "which gaps cost the most before Monday", "raise the exception list for the store", "what goes to the district manager". Do NOT use for product-content or listing completeness gaps — use the catalog enrichment completeness-score instead, or action-register instead for the fix order; not for the readiness test itself — use readiness-check instead; not for the checklist or shift brief — use brief-draft instead.
license: Proprietary
metadata: {version: "1.0.5", author: Microsoft Retail & CPG Skills, category: analysis, icon: Warning}
---
# Exception Raise

## Purpose
Deterministic ranking of store-launch readiness exceptions: weekly promo revenue at stake × launch proximity × price-conflict factor (`references/execution-rules.md` #5.1) — impact, not count. The engine ranks; this skill quotes.

## When to use
After readiness-check whenever anything in `checked.json` is missing or conflicted.

## When NOT to Use
- Gaps in product content — missing images, bullet copy, GTINs, attributes for a marketplace or channel listing — use the catalog enrichment completeness-score instead, or action-register instead for the fix order. This skill only knows store-launch readiness.
- "Are we ready" / "any gaps" (the test itself) — use readiness-check instead.
- Drafting the readiness checklist, shift brief or DM escalation text — use brief-draft instead.
- The pack or store records still need assembling — use pack-ingest instead for the pack, use store-map instead for the store records.

## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Files the user names, links or attaches in the chat.
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by campaign ID, store ID or file name when no location is given.
- Email attachments (for example a store manager's note) found the same way.

Read each source with the file reader (ReadFileContent) and cite it by file name and row or page. Write the working JSON files (`velocity.json`, `ranked.json`) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values.

## Inputs
`checked.json` (the `{readiness}` hop, from readiness-check or supplied by the user) + the sales velocity extract from the user's Microsoft 365 content (see *Where the data comes from*). Convert the extract to `velocity.json`, citing its rows, in exactly this shape: `{ "<SKU>": {"weekly_units": <n>, "promo_price": <price>} }`. Never estimate weekly units. Rules: `references/execution-rules.md` #5.1.

## Steps
1. Run the engine: `python scripts/exception_rank.py --checked checked.json --velocity velocity.json --out ranked.json`
2. Quote the ranking verbatim with the numbers. A small missing signage kit on the top-velocity SKU outranks five gaps on slow movers — say so with the revenue figures.
3. Flag the proximity factor (2× inside 3 days of launch) and the price-conflict factor (1.5×) from `provenance.ranking_factors`; top exceptions inside 3 days go to the district manager.
4. Validate the output with the contract validator tool: `python tools/validate_contract.py ranked.json`.

```bash
python scripts/exception_rank.py --checked checked.json --velocity velocity.json --out ranked.json
# exception_rank: 4 exception(s), top=PRICE-GTIN-2002, proximity=2.0x, price_conflict=1.5x -> ranked.json
```

## Output format
`ranked.json` — the `{exceptions}` hop. Report as a markdown table in engine order: # | req_id | status | detail | revenue at stake / week | rank score | citation; then one sentence on impact-vs-count with the figures; then the district-manager list. 

## Grounding requirements
Every exception cites its pack line (or price-file row) and the velocity extract.

## Guardrails
- Ranking is engine-only; never reorder, promote or demote an exception because a gap "looks small" or someone would rather the district manager did not see it.
- Never drop or hide a PRICE CONFLICT — it stays in the list and in `escalations[]` until HQ resolves the price file.
- Never estimate weekly units; if the velocity extract is missing, the engine fails closed — list the exceptions unranked and ask for the extract.
- Do not draft the brief here — hand `ranked.json` to brief-draft.
- Always show the ranked table for review before escalation goes anywhere.

## Escalation / uncertainty
Top exceptions within 3 days of launch carry the 2× proximity factor and go to the district manager. If `readiness.blocked` is true (#6), say the ranking is provisional until the missing input arrives.
