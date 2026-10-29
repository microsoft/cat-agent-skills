# Denials & Appeals Rules
Companion to deadline_engine (base/scripts/deadline_engine.py). Each numbered rule below is mirrored by one
named constant in the engine, line for line. Thresholds live in config/payer-appeal-windows.json, never in code.

## #1 Deadline is computed, never estimated
`deadline-track` computes deadline = denial_date + config.payers[payer].appeal_window_days exactly. It never
rounds or pads the number, and it always reports days_remaining relative to today - the real current date, or an
explicit `--today` date used only to reproduce a demo scenario's snapshot figures. `denial.as_of` is the contract snapshot date and
never stands in for today; when it differs from today the engine says so in escalations[]. If the payer has no entry in
config, no deadline is produced (deadline and days_remaining are null) and the denial is escalated to
payer-relations - a default window is never assumed. Payer names are matched against config case- and
whitespace-insensitively ("CONTOSO HEALTH PLAN" is Contoso Health Plan); a name that still matches nothing is
unconfigured. A deadline also needs a denial_date: when a configured window applies but denial_date is missing, the
engine stops with a readable error naming the claim and computes nothing - a date is never assumed.

Re-running the engine on a contract that already carries its escalations recomputes them rather than appending them
again: engine-written escalations appear once, with the current day count, and escalations written by other skills or
people are carried forward once, unchanged.

## #2 Coding integrity boundary - False Claims Act exposure
A coding_request is honoured only when the chart itself is cited: chart_evidence.citations must contain an entry
naming a specific note and date whose supports_code equals the requested code, **and**
chart_evidence.supports_requested_code must be true. A bare supports_requested_code flag is not evidence and is
never sufficient on its own. Otherwise the plugin refuses and reports the request as an **evidence gap for human
decision** - never a proposed code, never auto-applied. This is architectural, not a setting, because
unsupervised upcoding is a False Claims Act exposure, not a quality issue.

## #3 Queue ranking
When multiple denials are queued (queue[] on the contract), rank by (deadline ascending, recoverable_value
descending) - never by ease of appeal. Queue entries whose payer is unconfigured have no computable deadline and
sort last, but they are still ranked and still escalated; they are never dropped. When the primary denial's payer
is unconfigured, the queue row for that same claim is unconfigured too (ranked last, escalated naming the denial's
payer), even if the queue export spells the payer so that it matches config: a claim never gets a deadline the
denial itself does not have.

## #4 No-drop rule
A denial never leaves the queue because a coding change was refused. When a coding_request is refused under #2,
the denial stays queued on its original, chart-supported code and its deadline stays tracked, so the legitimate
appeal is not lost with the rejected recode. Removal from the queue is a human decision recorded outside this
plugin.

## #5 Draft-first boundary
The plugin drafts, calculates and ranks. It never submits, files, sends or closes an appeal, and never writes to
a claim or coding system. Action level L0 by default; any outbound act is L1 and belongs to a human.

## #6 Urgency flag
When days_remaining is at or below config.urgent_threshold_days, the denial is flagged for urgent queue
priority. The threshold is customer config, not an engine constant. The check applies to the primary denial AND to
every claim in queue_ranked[]; every result carries deadline_status (open | urgent | expired | unconfigured).

## #7 Expired state
When days_remaining is below zero the deadline has passed: deadline_status is `expired`, the claim is escalated for a
human decision, and it stays in the queue (never dropped, #4). A past deadline is never reported as time remaining.
