---
name: Case Preparation Brief
description: "Prepare a decision-ready support case brief with status, history, open commitments, and the recommended next step."
agentDescription: "Builds a decision-ready brief on one support issue, covering status, material history, open commitments, and the recommended next step. Use before the next interaction or action on one case, incident, ticket, customer issue, request, or complaint — reconciling what's happened, what's still open, and what to do next, even from a single description or one substantive interaction with no full record yet. Examples include \"brief me on this case\", \"prepare this case handoff\", and \"what is still open on this complaint\". Do not use to rank several issues, compose the outbound customer reply, or close, reassign, or otherwise change the case."
platforms: [Cowork]
category: service
builtByMicrosoft: true
tags: [customer-service, case-management, handoff]
author: Copilot Cowork team
authorUrl: "https://www.microsoft.com/en-us/copilot/features/cowork"
createdAt: 2026-10-31
---
# Case Preparation Brief

Domain: Customer Service.

Follow this skill's evidence, artifact, privacy, action-control, and outcome-reporting rules below.

## Evidence and connectivity

Begin with authorized user-provided material and accessible work sources. Discover optional CRM, knowledge, communication, quality, and workflow capabilities at runtime and use them only to enrich or execute the job; never require a vendor, connector, record identifier, object name, or field name when the minimum semantic evidence is otherwise available.

If a capability is unconfigured, unavailable, denied, stale, partial, or unsupported, continue with the supported baseline, disclose the affected scope, and block only the dependent conclusion or action. Distinguish an authorized empty result from failed or unexecuted retrieval. If no connected evidence source is available, ask for the minimum pasted facts or file needed for the next useful step and return a bounded framework or `needs_input` rather than inventing data.
Use supplied material and authorized issue, interaction, correspondence, attachment, entitlement, service-history, and policy sources that can affect the next interaction or action. Connected CRM is optional enrichment. Reconcile duplicated events, later evidence, open commitments, and conflicting status rather than treating record recency as substantive progress.

## Data Sources

Use relevant supplied material or applicable tools and sources you are authorized to access. These are options, not a mandatory checklist. Ask for missing essential input or context; unavailable evidence remains unknown, not negative evidence.

- Record Snapshots & Exports for issue description, status, action history and evidenced entitlement or response-time state.
- Email & Meeting Transcripts for substantive interactions, customer impact and accepted commitments.
- Internal Messaging for handoff context, unresolved dependencies and attributed prior actions.
- Knowledge & Files for attachments, applicable policies and supplied escalation or closure criteria.

Retain provenance, freshness limits and the existing evidence, privacy and authorization rules.

## Purpose
Prepare a decision-ready brief on one case, incident, ticket, customer issue, request, or
complaint before the next interaction or action — not an assumption that a solution
already exists. Reconciles the current problem and status, the material chronology, what
has actually been tried and its outcome, customer impact, unresolved obligations,
commitments/owners/deadlines, and contradictions, and closes with an evidence-backed
recommended next step. Replaces manually reconstructing that picture from scratch.

## Applicability
Applies to exactly one identified case, incident, ticket, issue, request, or complaint.
Minimum evidence is a subject plus an issue description, or one substantive interaction
(a message, call note, or complaint) — a full case record, a response-time timer, a case
identifier, and a complete logged history are not required. A brand-new issue with thin
evidence produces a bounded initial brief scoped to what is actually known, not invented
history; richer evidence (a fuller timeline, prior related issues, applicable policy)
deepens the same brief without changing what it does.

## Usage situations
- "Brief me before I respond to this."
- "What's the status of this issue, and what should happen next?"
- Handoff or reassignment — bringing a new owner up to speed before they act.
- Picking up an issue someone else worked on previously.
- Non-trigger: choosing or ranking among several open issues (use `case-triage`), or
  composing the actual outbound reply once the next step is decided (use `draft-customer-reply`).

## Decision criteria
Several kinds of judgment recur through this brief and are configurable by the
organization; apply supplied criteria when available, and otherwise reason conservatively
and mark the decision as depending on an unresolved threshold or rule rather than guessing
one:
- **Escalation / closure criteria** — what combination of unresolved obligation, customer
  impact, or elapsed time warrants escalation versus continued handling versus closure.
  When no such criteria are supplied, do not invent a default threshold, response-time
  number, or approval authority; instead present the escalation-relevant evidence and mark
  the escalation/closure decision as depending on organization-specific criteria that are
  not currently available.
- **Materiality / urgency criteria** — what counts as a material fact, a genuine
  contradiction, or an urgent condition for this kind of issue. Distinguish urgency that is
  directly observed in the evidence (an explicit deadline, a stated safety or business
  impact, repeated unanswered contact) from urgency merely inferred from tone or
  repetition — state which basis applies. Customer impact, outstanding commitments, and
  repeated unanswered contact can justify escalation attention even when no response-time
  state is available, without asserting that a breach has occurred.
- **Knowledge/policy authority** — which policy or knowledge source governs the
  recommended next step, when more than one could apply. Name the policy actually used
  when the evidence identifies one; otherwise note that authority as unresolved rather than
  picking one arbitrarily.
- Brief format and emphasis (which sections lead, how much chronology to show) may also be
  organization-specific; absent a stated preference, use the Output shape below.

## Procedure
1. Identify the case, incident, ticket, issue, request, or complaint unambiguously from
   what has been supplied.
2. Assemble the material chronology from available evidence, noting each attempted action's actual outcome. Distinguish facts refreshed this turn from supplied or recalled history and unresolved discrepancies. A recent-activity or response-time check verifies only what it returned; it does not freshly verify the entire older chronology. Retain useful prior context with its actual provenance.
3. Reconcile the current problem statement and status against that chronology; flag any
   genuine contradictions (per Decision criteria) rather than silently picking one version.
4. Identify customer impact, any unresolved obligations, and commitments/owners/deadlines
   already made — do not treat silence or an unanswered message as consent or resolution.
5. Assess urgency using the Decision criteria above: weigh applicable authoritative policy
   against the direct evidence in front of you; a more recent message does not
   automatically override a standing agreement or commitment.
6. Distinguish proposed, attempted, and verified resolution among any prior actions — a
   proposed fix is not the same as a confirmed outcome.
7. Determine a recommended next step using the escalation/closure and knowledge/policy
   criteria in Decision criteria; separate that recommendation from its supporting
   evidence, material alternatives, and any decision input that is missing.
8. Produce the brief per Output — a synthesis, not a raw timeline dump.

## Output

Deliver two parts: one concise chat summary and one saved primary editable artifact containing the complete internal case-preparation brief. The chat summary does not replace the saved artifact.

### Chat summary

In chat, state the current issue position, recommended next action, largest readiness risk or
unresolved fact, and what must be checked before the next customer interaction. Make the
evidence cutoff and unsupported coverage visible.

### Artifact content

- Current situation, in one or two sentences.
- Established facts and material chronology, with source and freshness attached to material claims; do not label a mixed-source brief as entirely verified live.
- What has been attempted, and its actual outcome.
- Customer impact and unresolved obligations, with commitments/owners/deadlines.
- Risk or urgency, with the evidence basis for it (see Decision criteria).
- Contradictions, unknowns, and any evidence that may be missing or stale, named rather
  than silently resolved.
- Recommended next step, its supporting evidence, material alternatives, and any missing
  decision input — kept clearly separate from anything already confirmed done.
- The scope and provenance of the evidence actually used (for example, "based on the issue
  description only" versus "based on the full logged history").

Identify audience, purpose, target, evidence cutoff, visible source scope, assumptions,
limitations, and validation outcome. Do not create a customer-facing artifact by default.

### Artifact selection

Choose the format for the complete internal case-preparation brief, respecting the user's requested format:

- **Word (.docx):** Default for the next owner to read and annotate before acting.
- **Excel (.xlsx):** Add a register when multiple commitments or handoff dependencies need filtering by owner, deadline or next check.
- **Markdown (.md):** When requested or Office creation is unavailable or fails; retain the full content and disclose fallback limitations.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Create and save the complete internal case-preparation brief in the selected format as the primary editable review artifact.

Verify each save before reporting success and provide the actual link or location. If saving fails, disclose it and provide clearly labeled unsaved preparation in chat.

## Guardrails
- Creating and saving the requested file artifact in an authorized location is permitted.
- This brief is an analysis and recommendation product: producing it does not close,
reassign, send a reply, promise compensation, or otherwise change the case's state.
- Do not report a follow-up as completed unless the evidence actually confirms it happened.
- Any action implied by the recommended next step — closing, reassigning, sending a reply, or
committing to a resolution — is a separate step outside this brief, and requires its own
explicit approval of what will happen and to whom; confirm before it is carried out.
- Do not fabricate history, commitments, or outstanding items when none exist; state
  plainly that the issue is new or thin rather than inventing content to fill the shape.

## When NOT to Use
- Not for ranking or choosing among multiple open issues; use `case-triage`.
- Not for composing the outbound customer reply; use `draft-customer-reply` with this
  brief's recommended next step and evidence as context.

## Required information
- **Baseline:** a subject plus an issue description, or one substantive interaction. Either
  is sufficient to produce a bounded initial brief.
- **Broader scope:** a fuller activity/interaction history, current response-time state,
  related issues for the same customer, and applicable policy each deepen the same brief
  without changing the procedure — they are more evidence to reconcile, not a different
  analysis, and their absence limits scope rather than blocking the brief.

## Representative prompts
- "Brief me before I respond to this ticket."
- "Bring me up to speed on this case before I take it over."
- "What's actually still open on this complaint, and what should happen next?"
