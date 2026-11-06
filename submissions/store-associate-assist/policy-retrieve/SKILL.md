---
name: policy-retrieve
description: 'Resolves the applicable policy clause and checks promotion eligibility deterministically with the policy_resolve engine (window AND cluster AND SKU). Use after question-intake on "what does the policy say", "is this return within the window", "can we price match this competitor", "is the customer eligible for the promo", "does the raincheck clause apply". Do NOT use for a fresh floor question with no question.json - use question-intake instead; not for a pure two-SKU spec comparison - use product-compare; not to present an already-computed promo result - use promo-check; not to draft the answer - use answer-draft.'
license: Proprietary
metadata: {version: "1.0.9", author: Microsoft Retail & CPG Skills, category: research, icon: BookSearch}
---
# Policy Retrieve
## Purpose
Deterministic clause resolution (#1) and the three-part promo eligibility test (#2.1). An exclusion clause outranks the general clause only when one of its distinguishing topics (marketplace, third-party, amazon, ebay) is in the question (#1.3).
## When to use
- After question-intake, when the question involves policy or promotion: returns, price match, rainchecks, promo eligibility, "what does the policy say".
## When NOT to use
- No `question.json` yet - question-intake first.
- Two SKUs and no policy question - product-compare.
- Presenting the promo result to the associate - promo-check. Drafting the answer - answer-draft.
- Policy areas the library does not cover (warranty, loyalty, staff purchase): the engine returns `out_of_scope`; escalate, never improvise.
## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Files the user names, links or attaches in the chat.
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by store ID, SKU/GTIN, product name, promo ID or file name when no location is given.
- Teams chat exports and email attachments (for example the associate's floor question) found the same way.
- The current promotions pack (PDF, Word, text or CSV) found by promo ID, SKU/GTIN or file name.
Read each source with the file reader (ReadFileContent) and cite it by file name and row or page. Write working files (`promo-pack.json`, `resolved.json`) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values (the values in the examples below are placeholders, not data).

## Inputs
- `question.json` from question-intake in this session (or supplied by the user).
- The promotions pack from the user's Microsoft 365 content (see *Where the data comes from*). Build `promo-pack.json` from it (step 2).
- Configuration (ships in this skill folder, configure before use): `config/policy-library.json` - the retailer's return, price-match and raincheck clauses with their topics. Contract: `contracts/rtl.store-associate-assist.v1.json` (`policy_resolution`, `promo_check`). Rules: `references/assist-rules.md`.
## Steps
1. Validate `question.json` against the contract (`contract_version`, `question.text`, `question.asked_on`, `question.facts`, `store_context.cluster` present). The engine reads receipt, stock and purchase date only from `question.facts`; if `facts` is missing, the engine stops with a contract error - send the question back to question-intake, never fill the facts here. Shape:
   ```json
   {"contract_version": "rtl.store-associate-assist.v1",
    "question": {"text": "<verbatim>", "topic": "raincheck", "asked_on": "2026-01-15", "sku": "GTIN-EXAMPLE-1", "compare_skus": [], "compare_attributes": [],
      "facts": {"receipt": "unclear", "stock_at_this_store": "out_of_stock", "purchase_date": null,
        "evidence": {"stock": "nothing on the shelf or in the back"}}},
    "store_context": {"store_id": "ST-0000", "cluster": "rural-compact", "department": "home", "source": "Store Master Export.csv row 7"},
    "escalations": []}
   ```
2. Build `promo-pack.json` in the session working folder from the user's promotions pack, one entry per promotion, verbatim values only, in exactly this shape (a JSON list):
   `[ {"promo_id": "<id>", "name": "<promotion name verbatim>", "skus": ["<GTIN>", ...], "clusters": ["<cluster>", ...], "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "citation": "promo pack <id>"} ]`
   Keep the pack's order. Tell the user which file and page or row each promotion came from. Never fill a missing window, cluster or SKU list; if the pack cannot be found, say so and ask.
3. Run the engine tool: `python scripts/policy_resolve.py --question question.json --policies config/policy-library.json --promos promo-pack.json --out resolved.json` (session paths for `question.json`, `promo-pack.json`, `resolved.json`).
4. Quote the clause id, text and determination verbatim. If `determination` is `excluded`, say which distinguishing topic triggered it; if `eligible_if_listed_competitor`, say the competitor must be on the listed set - execution is still a manager action (#2.2).
   Gated outcomes (`applicable_clause` is null): `no_alternative_in_stock`, `no_alternative_promo_not_eligible` (raincheck refused, #2.3); `escalate_stock_unknown`, `escalate_promo_unknown` (ask the associate, never offer a raincheck); `escalate_receipt_missing`, `escalate_receipt_unknown`, `escalate_category_not_covered` (return not resolved, #1.4). With clause RET-2.1: `not_eligible_outside_window` (purchase date outside the category window - not eligible) and `confirm_purchase_date` (no purchase date stated - quote "Eligible only if within <n> days of purchase - confirm the receipt date"; below the floor, never "eligible"). Never present any of these as eligible; an `escalate_*` outcome is a shift-lead escalation and a question back to the associate.
5. Read `escalations[]`: `out_of_scope` (#1.2), confidence < 0.75 (#4.1), missing date/cluster - each becomes a shift-lead escalation line, never an answer.
6. Hand off. In an end-to-end run the next hop is promo-check (it writes `promo-check.md`, which answer-draft copies) whenever the question mentions a promotion, deal, discount, offer, ad or raincheck, or `promo_check.checked` is true; then product-compare when `question.compare_skus` holds two SKUs; then answer-draft. Name the next hop in the hand-off line.
## Example
```
User: "Customer has a printed in-store price from a listed brick-and-mortar competitor for GTIN-EXAMPLE-1, ST-0000, 2026-01-15 - do we price match?"
-> policy_resolve: clause=PM-1.2 det=eligible_if_listed_competitor conf=0.9; promo P-0000-EXAMPLE not eligible (window ended 2026-01-14; cluster rural-compact not in ['urban-large'])
Reply: table clause | determination | condition text | confidence; promo table leg | pass/fail | reason; then "Price execution: manager action (#2.2)."
```
## Output format
`promo-pack.json` and `resolved.json` - the `{policy_resolution, promo_check}` hop - in the session working folder. In chat: a table (clause | determination | condition | confidence), the promo three-leg table with exact dates and the promotions-pack file and page, then the escalation lines if any. No floor script here - that is answer-draft.
## Grounding requirements
Every determination cites its clause id (or, for a gated outcome, the clause whose requirement was not met); promo results cite the promo pack line (#1.1) and the user's promotions-pack file and page or row. Nothing is stated that the engine output does not contain.
## Guardrails
- Resolution is engine-only: never relabel, soften or "round" a determination because the customer is waiting - if asked to, refuse and escalate.
- Never extend a promo window or cluster; never authorise a price match, refund or override (#2.2) - the skill informs, a manager executes.
- Never invent a clause for a topic the library lacks; `out_of_scope` goes to the shift lead (#1.2).
- Never state "approved" or "eligible" in the associate's words when the engine said otherwise.
## Escalation / uncertainty
If the policy library or the promotions pack cannot be read, stop and report the missing source; never quote a clause or a promo from memory. Confidence < 0.75 (multi-topic question) or no clause -> shift-lead escalation with the draft attached (#4.1). Missing `asked_on` / cluster -> promo marked unchecked; ask intake for the value.
