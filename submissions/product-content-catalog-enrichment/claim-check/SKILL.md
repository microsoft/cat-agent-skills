---
name: claim-check
description: Validates product marketing claims and regulated terms in supplier copy against the approved claim library for that GTIN and market - the explicit Govern step. Use after completeness-score, or when the user says "is this copy safe", "can we say antibacterial", "check the claims", "validate the marketing claims", "is this regulated wording allowed in <market>" or "do we have substantiation for <claim>". Do NOT use for trade-deduction, invoice or insurance claims - use claim-ingest / claim-match instead; do NOT use to approve or add a claim to the library - that is the claim owner's decision; do NOT use to draft copy - use content-draft instead.
license: Proprietary
metadata: {version: "1.0.5", author: Microsoft Retail & CPG Skills, category: analysis, icon: ShieldCheckmark}
---
# Claim Check (Govern)

## Purpose
The compliance determination IS the work. `scripts/claim_check.py` decides per GTIN and market: `approved` (library substantiation cited), `regulated_blocked` (#4.2), or `unapproved` (#4.1 scope mismatch / #4.4 romance term). Blocked claims never appear in copy, not even softened (#4.3).

## When to use
- After completeness-score, before any copy is drafted (`scored.json` exists).
- The user asks whether specific wording is safe/allowed for a product in a market.

## When NOT to Use
- "Retailer deducted from the invoice", "does this claim match what we signed" -> trade-deduction skills (claim-ingest, claim-match).
- Insurance, warranty or returns claims -> not this plugin.
- Completeness / missing fields -> use completeness-score instead. Copy or packets -> use content-draft instead.
- Approving a regulated claim, adding substantiation or editing `config/claim-library.json` -> claim owner / regulatory affairs, never this skill.

## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Files the user names, links or attaches in the chat (for example a `scored.json` from completeness-score, the supplier item sheet or a copy document).
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by enrichment batch ID (for example `ENR-0000-EXAMPLE`), supplier name, GTIN or file name when no location is given.
- Email attachments (for example a supplier email asking to "use the copy as written") found the same way.

Read each source with the file reader (ReadFileContent) and cite it by file name and row or page. Write the working JSON files (`scored.json` when you have to build it, `governed.json`, plus `governed-<market>.json` for each extra market) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values.

The approved claim library `config/claim-library.json` is retailer configuration owned by the claim owner; it ships with the plugin and is never edited here.

## Inputs
`scored.json` (the `{completeness}` hop, from completeness-score earlier in the session or supplied by the user) + `config/claim-library.json` + target `--market` (from the user's request or the enrichment request; if neither states it, ask - the engine's default is US). For an ad-hoc question about quoted copy or a single SKU in the user's files, build a minimal scored payload from that source and say so; the engine reads only these fields:
```json
{"contract_version": "rtl.product-content-enrichment.v1", "batch_id": "ENR-0000-EXAMPLE",
 "normalized": [{"gtin": "GTIN-EXAMPLE-1", "gtin_valid": true, "attributes": {"supplier_copy": "<supplier copy verbatim>"},
                 "unmapped": [], "source": "user copy", "citation": "<file name, row or page>"}],
 "escalations": []}
```
Set `gtin_valid` from attribute-normalize (run it on the GTIN first); never assume a GTIN is valid.

## Steps
1. Run the engine (tool: shell), once per market asked:
   ```bash
   python scripts/claim_check.py --scored scored.json --library config/claim-library.json --market US --out governed.json
   ```
2. Quote `claim_findings[]` verbatim: claim, verdict, detail, citation. Approvals cite the substantiation reference; blocks cite the regulated-term list; `unapproved` cites the scope mismatch or romance list.
3. Answer the user's question directly from the verdicts: "approved for <market A> (<substantiation ref>); blocked for <market B> (library markets: <market A>)". For a second market, re-run with `--market <code> --out governed-<code>.json`.
4. Records with `record_blocked: true` (invalid GTIN) are evaluated for the steward only - say that nothing from that record can be drafted until the GTIN is confirmed (#1.1).
5. Escalate every `regulated_blocked` finding to the claim owner with the library citation; hand `governed.json` to content-draft.

## Output format
A table: `GTIN | claim | verdict | market | substantiation / reason`, then a one-line answer per question asked, then a bulleted escalations list. Sections: Findings, Answer, Escalations, Next hop.

## Grounding requirements
Every verdict comes from the engine and cites the library entry or the regulated-term list. The model never issues a verdict of its own.

## Guardrails
- Never rephrase a blocked claim into acceptable-sounding copy - "fights germs" for a blocked "antibacterial", "kind to the planet" for a blocked "biodegradable" is still the claim (#4.3).
- Never approve a claim on a user's, category manager's or supplier's say-so; "their legal reviewed it" is not substantiation (#4.1).
- Never add, edit or drop entries in `config/claim-library.json`; route proposed substantiation to the claim owner and re-run after they record it.
- Never hand-author `approved` findings; only the engine writes `claim_findings`.
- If the library entry is missing for the GTIN and market, or `scored.json` cannot be read, the answer is "blocked / unapproved" plus an escalation - do not soften it to "probably fine".
- Review the findings table with the claim owner before content-draft uses the payload.

## Escalation / uncertainty
Every blocked claim -> claim owner with the library citation; blocked-record findings -> data steward.
