---
name: pipeline-prioritizer
description: Ranks a scoped set of open opportunities into an evidence-backed worklist of what to work next and why, with ties and unknowns where needed. Use when a scoped visible opportunity set needs a ranked or tied worklist explaining what deserves attention next and why, such as "which deals should I work today", "rank my open opportunities", or "prioritize this deal list". DO NOT use for change digests, meeting prep, or full team pipeline reviews.
metadata:
  displayname: Pipeline Prioritizer
---

# Pipeline Prioritizer

Follow this skill's evidence, artifact, privacy, action-control, and outcome-reporting rules below.

Domain: Sales.
## Evidence and connectivity

Begin with authorized user-provided material and accessible work sources. Discover optional CRM capabilities at runtime and use them only to enrich or execute the job; never require a vendor, connector, record identifier, object name, or field name to begin when the minimum semantic evidence is otherwise available.

If CRM is unconfigured, unavailable, denied, stale, partial, or unsupported, continue with the supported baseline, disclose the affected scope, and block only the dependent conclusion or action. Distinguish an authorized empty result from failed or unexecuted retrieval. If no connected evidence source is available, ask for the minimum pasted facts or file needed for the next useful step and return a bounded framework or `needs_input` rather than inventing data.

## Data Sources

Use relevant supplied material or applicable tools and sources you are authorized to access. These are options, not a mandatory checklist. Ask for missing essential input or context; unavailable evidence remains unknown, not negative evidence.

- Record Snapshots & Exports for the authorized opportunity set, ownership, open status and comparable dated values.
- Email & Meeting Transcripts for customer commitments, substantive engagement and decision timing.
- Internal Messaging for evidenced dependencies and interventions that could change the outcome.
- Knowledge & Files for supplied ranking criteria, staleness definitions and supported comparison assumptions.

Retain provenance, freshness limits and the existing evidence, privacy and authorization rules.

## Purpose
Turn a scoped set of open opportunities into a ranked worklist of what to work next and why
now, separating deals genuinely worth immediate attention from those that merely look large,
risky, or stale.

## Applicability
Use when a defined opportunity scope (an owner's book, a named team, or an explicit
account/deal set) and current opportunity evidence are available. Works as a standalone
ranking from supplied or exported evidence; a live engagement-history feed improves the
engagement read but is not required to produce a bounded, useful result.

A scope of one qualifying deal supports a bounded assessment without an invented peer
ranking. A checked scope with no qualifying deals is a valid result; missing input is not
an empty set. Peer ranking needs sufficient comparable evidence for the requested lens
across at least two deals; otherwise return ties, a limited ranking, or bounded assessments.

## Usage situations
- "Which of my open deals should I work today?"
- "Which deals need my involvement this week?"
- "Which opportunities have gone quiet and need a check-in?"
- Non-trigger: "what changed on my deals since last week" (use `deal-catchup`); "prep me for
  this meeting" (use `meeting-prep`); "give me the team's full pipeline review" (requires a
  separate team-level review procedure rather than this ranked worklist).

## Procedure
1. Establish the explicitly requested, authorized analysis scope: an owner's book, a named
   team/person, or an account/deal set. For a general ask, default only to verified
   responsibility, including others' deals only where accountability is established.
   Supplied documents establish neither ownership nor intent to access a wider book.
   Confirm material ambiguity; otherwise state a clearly bounded provided-set analysis
   without claiming accountability for those deals. Never make an unauthorized broad pull.
2. Establish the ranking lens the ask calls for, independent of scope:
   - a contact or throughput worklist of open deals to work through;
   - an intervention worklist of deals needing attention, considering value, risk, and urgency;
   - a low-observed-engagement worklist of open deals with no customer-facing activity
     observed in the checked sources beyond a stated staleness threshold.
   State the lens used; do not conflate it with scope — a manager and an individual seller can
   each request any lens over their own resolved scope.
3. Keep four timing choices separate: the action horizon (when to act), eligibility filters
   such as a requested closing period, the evidence cutoff/lookback, and the stale-activity
   threshold. Resolve explicit relative periods to concrete dates with timezone, and state
   how each applies. "Work this week" does not mean "closing this week." Without a requested
   close-date filter, consider the scoped open set regardless of close date. If a missing
   horizon materially changes priority, ask; otherwise state that it is unspecified and
   give a bounded assessment. Do not invent missing deal dates or a current-week default.
   State the evidence dates used; without a supported staleness threshold, stale status
   remains unknown even when last-observed activity can be reported.
4. Use available relevant state: owner, account, stage, likelihood, value/currency, close date,
   commitments, and last-known engagement. Mark missing fields unknown; missing value or
   stage does not block an evidenced urgent commitment. State the evaluated record count
   and retrieval boundary; a bounded read is not proof of complete scope coverage.
5. Establish engagement and momentum from actual activity or communication evidence for the
   candidates that matter to the requested lens. A low count of recorded engagement is not by
   itself proof of disengagement — it may only reflect what was logged, not what happened.
   For each source/response shape, validate one result before batching: locate the actual
   evidence and its record associations, provenance, and dates. Do not reuse a record-list
   extraction for a differently shaped context response. A missing or unrecognized evidence
   structure is an extraction failure, not an empty history; inspect the returned content or
   source contract and correct the extraction. If it remains unresolved, disclose the affected
   scope and use other supported criteria, leaving engagement qualified-unknown.
   Check relevant contact/deal coverage across the pertinent period and customer-facing
   channels. An additional independent source alone does not establish coverage. Deduplicate
   overlapping evidence, distinguish internal-only activity, and retain contradictions.
   Distinguish observed absence within checked sources from partial or inaccessible evidence;
   qualify absence by sources and dates, never assert global "no engagement." Where coverage
   or the threshold is insufficient, classify engagement/staleness as qualified-unknown.
   Distinguish a newly opened deal from a stalled one.
6. Rank using organization-supplied or explicitly stated criteria across value, urgency
   (closeness and pace to a decision), risk, momentum/engagement, influenceability (whether an
   available action can actually change the outcome), and any explicit commitment made to the
   customer. Without organization-supplied weights or thresholds, reason qualitatively and
   state ties or unknowns as such — do not invent a numeric formula and present it as an
   organizational standard. A large value is not automatically the top priority; a flagged risk
   is not automatically worth intervening on unless an available action can plausibly change
   its outcome; a cold, late-stage deal is not automatically the top priority by stage alone —
   consider whether evidenced late-stage silence makes a useful re-engagement priority
   rather than automatically ranking it down.
7. Treat any recorded likelihood or probability value as informational, not as a number to
   project forward. An unknown or stale likelihood stays unknown; do not multiply or derive a
   forecast figure from it.
8. Compose a ranked worklist with a concrete, one-line "why now" per deal citing the specific
   factors that earned its position. State the lens, the scope and its known size, the evaluated
   record count, and any truncation.

## Judgment
- Value, risk, and staleness are each one input to priority, not priority itself. Rank by
  evidenced influenceability — whether an available action can actually change the outcome —
  not by raw size, a risk label, or stage alone.
- Attribute each row's owner from ownership evidence, or mark unknown; engagement is not
  ownership. Verified accountability governs a default scope, not every explicitly
  authorized analysis set. Neither title nor possession of evidence widens access intent.
- Distinguish scoped observed absence from unconfirmed engagement. Logged activity measures
  what was recorded; insufficient verification leaves the deal qualified-unknown, not dark.
- One qualifying deal in scope earns a real, bounded assessment of why it matters now; it does
  not earn a fabricated rank against peers that were never evaluated. A checked empty
  qualifying set is meaningful; missing input does not establish that result.
- A ranked list only reflects the deals actually evaluated. When the underlying read is bounded
  or paged, state that boundary — never present a partial read as the genuine top of the full
  scope.
- Compare values only on compatible currency/time bases or with a stated sourced conversion.
  Missing data may justify ties or limited comparisons, not fabricated scores.
- This procedure may propose an outreach priority for review. It does not contact anyone;
  execution needs its own separate authority and approval.

## Output

Deliver both a concise chat summary and one saved primary editable artifact, following the
sections below. The artifact must contain a ranked worklist, allowing ties or bounded assessments.

### Chat summary

In chat, summarize the highest-priority deal or tied group, the strongest "why now," the largest
coverage or comparison limitation, and the next action. State the lens, visible-set denominator,
and action horizon so the result cannot be mistaken for a full-pipeline forecast.

### Artifact content

State the lens, resolved scope and known size, action horizon, eligibility filters, evidence
cutoff/window, staleness threshold or its absence, evaluated count, and coverage boundary.
Then give a ranked or tied/limited table (deal, owner or unknown, account, stage, value and
currency, close date, "why now"), marking unavailable fields unknown. Explain qualified-unknown
engagement; distinguish a checked empty result from unevaluated candidates.

## Artifact selection

Choose one format for the complete internal visible-set prioritization, respecting the user's requested format:

- **Excel (.xlsx):** Default for filtering the ranked or tied worklist and inspecting evidence, criteria and supported alternate views.
- **Markdown (.md):** When requested or Excel creation is unavailable or fails; retain the full table and narrative, disclosing lost filtering or calculation.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Verify the save before reporting success and provide the actual link or location. If saving fails, disclose it and provide the full table and narrative as clearly labeled unsaved content in chat.

## Guardrails
This procedure is read-only except for creating and saving the requested file artifact in
an authorized location: it proposes a worklist and reasoning, and does not execute the worklist.
Contacting a customer, changing a record, or reassigning ownership each requires its own
explicit, separately authorized action — proposing that a deal be called or emailed is not the
same as placing the call or sending the message, and this procedure does neither.

## When NOT to Use
- Not for reporting what changed on a set of deals since a point in time; use `deal-catchup`.
- Not for a customer-interaction brief; use `meeting-prep`. Seller coaching agendas are outside this skill's scope.
- Not for a full team pipeline review with diagnosis across value, timing, coverage, and
  manager decisions. This procedure produces only a scoped prioritization worklist.
- Do not rank a scope that was never stated, and do not present a bounded or paged read as
  complete coverage of a larger book.

## Required information
- **Minimum:** a defined authorized scope, a resolved lens, and sufficient relevant evidence
  for that prioritization. No universal stage/value/close-date checklist gates the result.
- **Optional enrichment:** dated engagement/communication evidence for the candidates that
  matter to the lens, and organization-supplied ranking criteria (weights, thresholds,
  staleness definitions). Missing enrichment limits confirmation of engagement-based flags to
  qualified-unknown; it does not block a bounded, useful ranking.
- **Missing-input question:** "Which deals or portfolio should I prioritize?"
