---
name: deadline-track
description: "Deterministic engine: calculates the appeal deadline and days remaining from today, flags urgent and expired deadlines on every queued claim, ranks the queue by deadline then recoverable value, and enforces the coding-integrity boundary. Use when asked \"when is this appeal due\", \"how many days do we have left\", \"which denial should we work first\", \"can we recode this to a 99215 and refile\", \"that payer isn't in our config, just use 30 days\". Run before appeal-draft and again as the last step of every run. Do NOT use for drafting the letter - use appeal-draft instead; do NOT use for gathering evidence - use evidence-assemble instead; do NOT use for payer policy - use policy-retrieve instead. Never applies a coding change: refused recodes go to a human as an evidence gap. Action level L0: calculates and ranks only."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Revenue Cycle", action_level: L0, max_action_level: L1, icon: CalendarClock}
---
# Deadline Track
## Purpose
Guarantee no appeal is missed on a technicality, no denial is quietly dropped, and no coding change is smuggled through.
## When to use
Use before appeal-draft (so the letter knows the coding_decision and the clock) and again as the last step of every run, on every denial, whether or not a coding_request exists - typical asks are "when is this appeal due", "how many days are left", "which denial do we work first", "can we recode this and refile at the higher level".
## When NOT to Use
Do NOT use when: the ask is to write or reword the appeal letter - use appeal-draft instead; the ask is to find chart evidence - use evidence-assemble instead; the ask is about payer policy - use policy-retrieve instead; the ask is to change, extend or negotiate a payer's appeal window, or to assume one for an unconfigured payer; the ask is to re-order the queue by ease, effort or "quick wins"; or the ask is to apply, file or approve a coding change - this skill decides whether a recode may be honoured, and never performs one.
## Inputs
denial.denial_date; denial.payer; denial.recoverable_value; queue[]; config/payer-appeal-windows.json; coding_request (if any); chart_evidence with its citations; policy_citations.
## Steps
1. Run the engine tool - `python3 base/scripts/deadline_engine.py --question <contract.json> --payers config/payer-appeal-windows.json --out <result.json>` - with NO `--today` flag, so days are counted from the real current date. `--today` exists only to reproduce a demo scenario's snapshot figures; never pass it in a live run, and never compute a deadline by hand or by estimate.
2. If a coding_request is present, the engine honours it only when chart_evidence.citations names a specific note and date for the requested code (compared on the code itself, so "99215 (higher E/M level)" matches "99215") and supports_requested_code is true; otherwise coding_decision=refused_evidence_gap and the evidence gap is logged.
3. The engine ranks queue[] into queue_ranked by deadline ascending then recoverable_value descending, and gives every row a deadline_status.
4. The engine flags urgent (days_remaining at or below config.urgent_threshold_days) and expired (days_remaining below zero) for the primary denial AND every queued claim, and echoes the policy clause_ids into deadline_result.policy_basis.
5. Payer names are matched to config case-insensitively, so "CONTOSO HEALTH PLAN" uses the Contoso Health Plan window; re-running the engine on a contract that already carries escalations recomputes the engine's own escalations instead of duplicating them, and keeps every other escalation once.
6. Report deadline_status first, then the engine's numbers and escalations verbatim to the coordinator. If the engine reports that the contract as_of differs from today, say which date the figures are computed as of.
## Example
```
$ python3 base/scripts/deadline_engine.py --question contract.json --payers config/payer-appeal-windows.json --out result.json
deadline_engine: deadline=2026-09-19 days_remaining=-6 status=expired as_of=2026-09-25 coding=not_requested queued=3
Reply: "EXPIRED - CLM-10021's appeal deadline (2026-09-19, Contoso 30-day window) passed 6 days ago. Escalated for a
human decision; the claim stays queued. Queue (deadline, then value): 1 CLM-10052 ... 2 CLM-10021 ... 3 CLM-10044 ..."
```
## Output Format
Format: `deadline_result` on contract hls.denials-appeals-response.v1 - {deadline, days_remaining, deadline_status (open|urgent|expired|unconfigured), coding_decision (not_requested|supported_by_chart|refused_evidence_gap|n/a), coding_evidence_basis, policy_basis[], action_level, source} - plus `queue_ranked[]` of {rank, claim_id, payer, deadline, days_remaining, deadline_status, recoverable_value, rank_basis} and any strings appended to `escalations[]`. Prose reply sections: status line (EXPIRED / URGENT / open), ranked queue as a markdown table, escalations as bullets - every figure copied unchanged from the engine.
## Grounding requirements
Deadline arithmetic is exact date math against config, counted from today, not an estimate; the coding decision names the cited note and date it rests on. Do not fabricate, adjust or round any number outside the engine, and never state a deadline, day count or rank the engine did not output - on the unconfigured-payer path the answer is "no deadline can be computed", never an invented one.
## Guardrails
Guardrails for this skill:
- A past deadline is never reported as time remaining: a negative days_remaining is reported as EXPIRED, first, in every reply.
- Never extend or shorten a payer's configured appeal window, and never assume a window for a payer that is not configured.
- Never set coding_decision to supported_by_chart on a supports_requested_code flag alone; a cited chart note and date for that exact code is required - this is architectural, not a setting (denials-rules.md #2).
- Never apply, file or propose a coding change; a refusal is reported for human decision, never executed.
- Never rank the queue by ease of appeal, and never re-order it on request; deadline then recoverable value is the only ordering (denials-rules.md #3).
- Never remove a denial from the queue because a recode was refused or the appeal looks weak; de-queueing is a human decision made outside this plugin (denials-rules.md #4).
- Include only the identifiers the queue needs (claim ID, payer, dates, amounts); never output SSNs or unrelated patient data.
- Action level L0 (draft-only): this skill never submits, files, sends or closes an appeal and never writes to a claim or coding system. Anything that leaves the building is L1, performed by a human after review before it leaves (denials-rules.md #5).
## Error Handling
- Any refused coding_request is logged as an evidence-gap-for-human-decision escalation, routed to [TO CONFIGURE: physician advisor / coding compliance contact], and the denial stays queued on its original code (denials-rules.md #4).
- A payer with no entry in config/payer-appeal-windows.json (compared case-insensitively) yields deadline=null, days_remaining=null and deadline_status=unconfigured - no default window is ever assumed - and is escalated to [TO CONFIGURE: payer-relations contact]; the claim is still ranked (last, after every claim with a computable deadline) and never dropped (denials-rules.md #1, #3).
- An expired deadline (#7) is escalated to [TO CONFIGURE: appeals manager contact] for a human decision on next steps; the claim is never dropped and no late-filing option is asserted by this plugin.
- An urgent deadline (#6) on the primary denial or any queued claim is escalated as urgent queue priority.
- When the denial's payer is unconfigured, the primary claim's own queue row is unconfigured too, even if the queue export spells the payer so that it matches config - it never shows a deadline the denial itself does not have (denials-rules.md #3).
- A missing denial_date (on the denial, or on a queued claim with a configured payer) makes the engine exit 1 with a readable "deadline_engine: error: denial_date is missing for claim ..." message; no deadline is assumed (denials-rules.md #1).
- If the engine exits non-zero or the config file is missing, report the error verbatim and stop - never fall back to hand arithmetic.
