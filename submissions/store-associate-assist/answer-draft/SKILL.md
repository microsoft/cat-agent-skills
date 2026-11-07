---
name: answer-draft
description: 'Drafts the cited floor answer for the associate - or the shift-lead escalation when the payload is out of scope or below confidence - from the completed rtl.store-associate-assist.v1 payload, using the answer template. Use to close every assist run: "draft the floor answer", "write up the answer for the associate", "close out the assist run", "draft the escalation to the shift lead", "what can I tell the customer". Do NOT use for a new question with no resolved payload - use question-intake instead; not to compute eligibility - use policy-retrieve or promo-check; never send, post or execute anything - drafts only.'
license: Proprietary
metadata: {version: "1.0.9", author: Microsoft Retail & CPG Skills, category: writing, icon: Compose}
---
# Answer Draft
## Purpose
Terminal artifact: a floor-ready answer with the source shown, or an escalation record. Payload in, draft out - nothing added.
## When to use
- End of every assist run, once `resolved.json` / `compared.json` exists.
## End-to-end order (this skill is the closing hop)
When the user asks to run a floor question end to end, the hops run in this order, each from its own skill folder, sharing the session working folder:
1. question-intake -> `question.json`.
2. policy-retrieve -> `resolved.json`.
3. promo-check - ALWAYS when the question mentions a promotion, deal, discount, offer, ad or raincheck, or `promo_check.checked` is true in `resolved.json`.
4. product-compare - when `question.compare_skus` holds two SKUs -> `compared.json`.
5. answer-draft (this skill).
Before drafting, check that every step that applies has run (step 0 below). This skill never builds the promo table itself: the table comes only from promo-check's `promo-check.md`.
## When NOT to use
- A fresh floor question with no payload - question-intake, then policy-retrieve.
- Computing or re-checking eligibility - policy-retrieve / promo-check. Building the comparison - product-compare.
- Sending the answer to a customer, posting to POS, emailing or messaging anyone - not this plugin (drafts only).
## Where the data comes from
This plugin ships no sample data. Every input is the user's own Microsoft 365 content:
- Files the user names, links or attaches in the chat.
- Their OneDrive or SharePoint, found with Work IQ search (Microsoft 365 search) by store ID, SKU/GTIN, product name, promo ID or file name when no location is given.
- Teams chat exports and email attachments (for example the associate's floor question) found the same way.
- A completed payload file (`compared.json` or `resolved.json`) the user names or attaches, when the earlier skills did not run in this session.
Read each source with the file reader (ReadFileContent) and cite it by file name and row or page. Write working files (`ANSWER-<store id>-<asked_on>.md`, the draft) to the session working folder, never into the plugin. If a required source cannot be found, say which one is missing and ask the user where it is. Never invent it, estimate it or fall back to example values (the values in the examples below are placeholders, not data).

## Inputs
- The full contract payload: `compared.json` (or `resolved.json` when no comparison ran) from the earlier skills in this session, or a payload file from the user's Microsoft 365 content (see *Where the data comes from*).
- Ship in this skill folder: `references/answer-template.md` (skill-specific), `references/assist-rules.md`, `contracts/rtl.store-associate-assist.v1.json`.
## Steps
0. Promo-check gate (before anything else). Promo results are expected when the question mentions a promotion, deal, discount, offer, ad or raincheck, or `promo_check.checked` is true in the payload. If they are expected and `promo-check.md` is not in the session working folder, run promo-check now as its own hop, from its own skill folder, on the same payload (it writes `promo-check.md`), then continue. If promo-check cannot be run, stop: say "promo-check has not run for this payload - run promo-check, then answer-draft" and draft nothing. Never construct the three-leg table or the alternative line yourself from `promo_check`.
1. Validate the payload against the contract; if `policy_resolution.in_scope` is false, `confidence` < 0.75, or `escalations[]` is non-empty, the escalation section leads (#1.2, #4.1).
2. Fill `references/answer-template.md` section by section: determination(s) with citation, promo result, comparison table, "what you can / cannot do" with manager actions flagged (#2.2), customer script, shift-lead escalation when warranted.
   2a. Comparison: section 3 is written ONLY when `product_comparison.rows` is non-empty. When `rows` is empty or `product_comparison` is absent, omit section 3 entirely, heading included: no "## 3. Comparison" heading, no "not applicable", "no comparison requested" or "none" line, no mention of a comparison anywhere in the draft. Do not renumber: the sections that follow keep their template numbers (4, 5, 6), so the draft goes from section 2 to section 4.
   2b. Promo results are REQUIRED in the draft whenever they are expected (step 0): section 2 carries the three-leg table (window | cluster | SKU) and the alternative line copied verbatim from `promo-check.md`. Do not rebuild, reword or recompute them. When `promo-check.md` says "Promo: not checked - <reason>", copy that line instead. When promo results are not expected, write "Promo: not checked - <reason>" from `promo_check`.
3. Payload-only check: re-read the draft sentence by sentence; every fact must trace to a payload field, the cited clause text, or assist-rules.md. Delete anything else (raw-chat details such as seller names, paraphrases of clauses not in `policy_resolution`, prices not in the payload). Record `checked: payload-only` in the draft footer.
   `question.text` is the associate's own words, not a source for the draft: it tells you what was asked, never what to say. Do not quote or paraphrase anything from it except the product name or SKU. In particular leave out associate asides, hearsay and prior-practice claims - what a former manager or other staff "always did" or "used to do", what another store or colleague does, what the customer says they were told before - and any competitor price or seller name the payload does not carry. The draft states only the policy determination, its conditions, the promo result, the comparison, what the associate can and cannot do, the customer script and the escalation. Last check: compare the finished draft with `question.text`; delete any sentence that repeats its words beyond the product name or SKU.
4. Mark DRAFT and write it to the session working folder; the associate reads it, a manager executes any price, refund or promo action.
## Example
```
User: "Close out the run - draft the floor answer from compared.json."
-> step 0: promo_check.checked true, promo-check.md not in the session folder -> run promo-check (own skill folder) -> promo-check.md written
-> in_scope true, confidence 0.9, escalations [] -> answer path
-> Determination: price match EXCLUDED [policy clause PM-1.4]; promo P-0000-EXAMPLE NOT eligible [promo pack P-0000-EXAMPLE] window 2026-01-01..2026-01-14 vs 2026-01-15; cluster rural-compact not in ['urban-large']
-> promo table and alternative line copied from promo-check.md: window fail | cluster fail | SKU pass; "Alternative: none - applicable clause is not PRC-3.3"
-> product_comparison.rows is empty -> section 3 omitted, heading included; next section is "## 4. What you can / cannot do"
-> customer script + "MANAGER ACTION: any price decision (#2.2)" + shift-lead note (customer pressing) - no quote of the associate's asides
Reply: the filled template as markdown; footer "DRAFT - checked: payload-only".
```
## Output format
Markdown following `references/answer-template.md` sections 1-6 (section 3 only when `product_comparison.rows` is non-empty; otherwise sections 1, 2, 4, 5, 6), saved as a DRAFT in the session working folder. Citation format: `[policy clause <id>]`, `[promo pack <id>]`, `[PIM extract <gtin>]`, `[assist-rules.md #<n>]` after the sentence it supports. In chat: the draft, then one line naming the escalation status.
## Grounding requirements
No sentence without a citation available on request (#1.1). Nothing in the answer that is not in the contract payload, the cited clause text or assist-rules.md.
## Guardrails
- Never repeat the associate's asides, hearsay or prior-practice claims from the question text (what a former manager or other staff used to do); state only the determination, its conditions and the escalation.
- Never drop the promo-check table or alternative line when promo results are expected, and never build them yourself: they come only from `promo-check.md` (step 0 runs promo-check when it is missing).
- Never keep an empty comparison section: no "## 3. Comparison" heading or placeholder when `product_comparison.rows` is empty.
- Answers and drafts only: never override a price, authorise a refund, reserve inventory or change a schedule (plugin boundary); never write "approved" or "authorised" unless the payload's determination says eligible AND a manager is recorded as executing it - which this plugin never records.
- Never send, email, post or message the draft anywhere; if asked to, refuse and show the draft here instead.
- Never fabricate a clause, date, price or availability; a missing field is written as `not in payload`.
- Never include customer personal or payment data; the payload does not carry it and neither does the draft.
## Escalation / uncertainty
Anything the associate cannot resolve at their role level is drafted as a manager escalation with the payload citations attached. If the payload is missing `policy_resolution`, stop and route back to policy-retrieve - never decide here. If the template cannot be read, report it; do not free-write.
