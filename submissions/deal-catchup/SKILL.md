---
name: deal-catchup
description: Summarizes what changed and why across a scoped deal set, separating genuine customer movement from record housekeeping. Use to report what changed and why across a scoped set of deals since a stated baseline, such as "which deals slipped", "what moved on my top deals", or "what changed while I was out". Needs a defined scope and current deal evidence; a baseline improves the comparison, but a current-state result is available without one. DO NOT use for ranking what to work on next or a single deal's full standing review.
metadata:
  displayname: Deal Catch-up
---

# Deal Catch-up

Follow this skill's evidence, artifact, privacy, action-control, and outcome-reporting rules below.

Domain: Sales.
## Evidence and connectivity

Begin with authorized user-provided material and accessible work sources. Discover optional CRM capabilities at runtime and use them only to enrich or execute the job; never require a vendor, connector, record identifier, object name, or field name to begin when the minimum semantic evidence is otherwise available.

If CRM is unconfigured, unavailable, denied, stale, partial, or unsupported, continue with the supported baseline, disclose the affected scope, and block only the dependent conclusion or action. Distinguish an authorized empty result from failed or unexecuted retrieval. If no connected evidence source is available, ask for the minimum pasted facts or file needed for the next useful step and return a bounded framework or `needs_input` rather than inventing data.

## Data Sources

Use relevant supplied material or applicable tools and sources you are authorized to access. These are options, not a mandatory checklist. Ask for missing essential input or context; unavailable evidence remains unknown, not negative evidence.

- Record Snapshots & Exports for scoped membership, dated baselines, current state and authoritative change events.
- Email for substantive customer explanations of timing, value or decision changes.
- Meeting Transcripts & Notes for dated commitments and the reasons behind material movement.
- Internal Messaging for evidenced alignment needs, dependencies and seller-reported context.
- Knowledge & Files for prior reviews and proposals that establish a comparable baseline.

Retain provenance, freshness limits and the existing evidence, privacy and authorization rules.

## Purpose
Report what changed on a scoped set of deals since a stated point in time, distinguish genuine
customer or deal movement from record housekeeping, and attach a substantiated reason to each
material change.

## Applicability
Use when an account or a scoped set of deals is identifiable from the request, accessible work
context, or supplied material. Establish the requested comparison window and any available
baseline. Current structured deal state is optional enrichment, not a prerequisite. Two related
asks share this procedure:
- which deals in scope slipped, and why;
- what changed across a bounded top set of deals (by value or another stated basis) since a
  point in time.

A missing baseline or authoritative opportunity snapshot still supports a result: reconstruct
the dated visible-evidence chronology, label current structured state and period-over-period
movement unknown where unsupported, and do not invent a prior state. Disambiguate an opportunity
only when several plausible deals would materially change the result.

## Usage situations
- "Which of my deals slipped this week, and why?"
- "What changed on my top deals since last Monday?"
- "What moved on this account's deals while I was out?"
- Non-trigger: "Which deals should I work next" (ranking — use `pipeline-prioritizer`); "give me
  the full picture on this one deal" (a single deal's standing review).

## Procedure
1. Establish the account or deal scope and the baseline or window from the ask. Discover the
   account from available context before asking "Which account?" Resolve a relative period
   ("last week", "since I was out") to a concrete date
   range with timezone and state it. If the period is ambiguous, ask when material or state
   a provisional interpretation. Do not invent a prior state when a baseline is unavailable.
   For a bounded top set, name the selection basis and presentation cap; honor a supplied
   cap, otherwise state a practical cap for this result, not a universal priority threshold.
2. Use available current state for each in-scope deal: name, value, stage/status, close date,
   last record-modification time, owner, account, and stakeholders. Mark missing fields unknown.
3. Establish what changed:
   - Prefer a genuinely dated, authoritative history of the record when one exists.
   - Where a computed or narrative "what changed since" summary is available, treat it as a
     lead pointing at what to check, not a verified fact — it is generated, not a sourced
     quote.
   - Compare dated prior and current evidence, or use an authoritative dated change event.
     A modification timestamp establishes record recency only, not a specific deal change,
     direction, magnitude, or cause.
   - Report an in-window slip only when dated evidence places a postponement or a newly
     crossed close deadline while the deal remained open inside that window. Already
     overdue before the baseline is a separate current overdue status, not a new slip.
     Apply the same timing test to stage regression, likelihood/value decline, and won/lost
     transitions. If evidence brackets only a broader interval, state it and leave change
     inside the requested window unknown.
4. Establish why each material change happened from actual evidence — supplied notes, messages,
   meeting records, or other communication — read at the content level, not inferred from a
   status field alone. Attribute the reason to its source and, where known, the person. A
   change with no available evidence for its reason is still reported, with the reason marked
   unknown; an unconfirmed reason on one deal does not block reporting the rest of the digest.
5. Compare a source-attributed signal with established current record state before flagging
   it as not reflected in the record. Without that comparison, label it an unverified update
   candidate. Do not apply an update.
6. Compose per deal: what changed, the substantiated (or marked-unknown) reason, any
   record-update flag, and a suggested next action. When the evidence surfaces an
   internal alignment need or dependency that changes the next step, name it as an
   optional field distinguishing a known dependency, a decision still needed, and a
   suggested seller action — never a guessed colleague or area of expertise. Order by
   the stated impact basis (slip severity, value, or another stated criterion).

## Judgment
- A record-modification timestamp establishes recency only. Use dated change evidence to
  establish movement and substantive evidence to establish its cause.
- A generated "what changed" narrative is a lead to verify, not a verified source fact; cite
  the actual evidence, not the narrative, for the reason.
- An absent reason is a per-deal gap, not grounds to withhold the rest of the digest. Report
  the change and mark the reason unknown.
- Do not claim "no changes" or "all signals reviewed" unless the evaluated coverage actually
  supports it — state what was checked.
- A missing baseline yields a current-state, dated observation, with movement explicitly
  marked unknown — never a fabricated prior state or an invented "no change" result.
- State the selection basis, presentation cap, and comparison period used. A cap controls
  presentation, not business importance; a different cap, named list, or window is valid.
- A stated "top" set reflects the deals actually evaluated. When the underlying evidence pull
  is itself bounded or paged, say so — a partial read is not the genuine top of the full book.

## Output

Deliver both a concise chat summary and one saved primary editable artifact, following the
sections below. The artifact must explain what changed and why across a scoped deal set, marking unsupported movement or
causes unknown.

### Chat summary

In chat, summarize the largest evidenced movement, its best-supported reason, the most material
regression or unknown, and the next action. State the examined scope and window so the summary
cannot be mistaken for a complete portfolio view.

### Artifact content

Identify the ownership or membership evidence that establishes the requested deal set. Separate verified members from unresolved candidates; correspondence alone does not establish ownership. Preserve supported observations for candidates without including them in unqualified portfolio claims or asserting movement outside the verified baseline and period.

State scope, requested window, available baseline (or its absence), selection basis/cap,
evaluated deal count, and coverage. Then, per deal: verified movement and its dates, or
current state with change unknown; the substantiated reason (or "unconfirmed" with what
was checked); any record-update flag or unverified candidate; an optional internal
dependency field when the evidence supports one; and a proposed next action. Keep
existing overdue status separate from verified in-window slips.

## Artifact selection

Choose one format for the complete internal deal catch-up, respecting the user's requested format:

- **Word (.docx):** Default for explaining what changed, why and what to do next.
- **Excel (.xlsx):** Instead for filtering a scoped multi-deal chronology or action handoff, with takeaways and causal explanations retained.
- **Markdown (.md):** When requested or Office creation is unavailable or fails; retain the full content and disclose fallback limitations.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Verify the save before reporting success and provide the actual link or location. If saving fails, disclose it and provide clearly labeled unsaved catch-up in chat.

## Guardrails
This report is read-only except for creating and saving the requested file artifact in an
authorized location. It does not update records, send messages, or take any other action on a
customer's or seller's behalf. A record-update flag is a proposal for the user to apply, not an
applied change.

## When NOT to Use
- Not for choosing which deals to work next; use `pipeline-prioritizer`.
- Not for one deal's complete standing review; that requires a separate review procedure outside this catalog.
- Do not report a change as confirmed from a record-modification timestamp alone, and do not
  claim complete coverage from a partial or capped evidence pull.

## Required information
- **Minimum:** an identifiable account or deal scope. Accessible correspondence, meetings,
  notes, proposals, or supplied material can support a visible-evidence reconstruction without
  a current CRM opportunity snapshot.
- **Structured-state enrichment:** current opportunity evidence improves current-state and
  field-level comparisons but is not required for the baseline catch-up.
- **Comparison evidence:** a resolved comparison period plus dated prior/current evidence
  or a dated change event establishes movement within that period. Without it, report
  current state and dated observations, with change unknown.
- **Reason evidence:** substantive notes, messages, meeting records, or other evidence.
  Its absence leaves the reason unknown for that deal, not the whole result unavailable.
- **Missing-input question:** "Which account or deal set should I catch up on?"
