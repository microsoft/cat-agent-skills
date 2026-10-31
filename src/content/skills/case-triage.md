---
name: Case Triage
description: "Prioritize support issues using impact, deadlines, commitments, and evidence-backed urgency."
agentDescription: "Ranks support issues into an explainable work order based on impact, deadlines, commitments, and evidenced urgency. Use when two or more tickets, incidents, issues, requests, or complaints need an explainable relative work order based on impact, deadlines, commitments, staleness, unanswered contact, documented urgency, and any available priority or response-time evidence. Also supports a bounded urgency assessment for one issue without inventing a queue rank. Examples include \"rank these cases\", \"which complaint should be first\", and \"how urgent is this issue\". Do not use for a deep brief on one selected issue or to claim work automatically."
platforms: [Cowork]
category: service
builtByMicrosoft: true
tags: [customer-service, triage, prioritization]
author: Copilot Cowork team
authorUrl: "https://www.microsoft.com/en-us/copilot/features/cowork"
createdAt: 2026-10-31
---
# Case Triage

Domain: Customer Service.

Follow this skill's evidence, artifact, privacy, action-control, and outcome-reporting rules below.

## Evidence and connectivity

Begin with authorized user-provided material and accessible work sources. Discover optional CRM, knowledge, communication, quality, and workflow capabilities at runtime and use them only to enrich or execute the job; never require a vendor, connector, record identifier, object name, or field name when the minimum semantic evidence is otherwise available.

If a capability is unconfigured, unavailable, denied, stale, partial, or unsupported, continue with the supported baseline, disclose the affected scope, and block only the dependent conclusion or action. Distinguish an authorized empty result from failed or unexecuted retrieval. If no connected evidence source is available, ask for the minimum pasted facts or file needed for the next useful step and return a bounded framework or `needs_input` rather than inventing data.
Use the complete authorized visible set when available, or preserve the actual filter, page, cap, and coverage boundary. CRM queue access is optional; supplied lists, exports, correspondence, or issue summaries can support bounded triage. Preserve missing priority, deadline, commitment, impact, and response evidence as unknown rather than neutral.

## Data Sources

Use relevant supplied material or applicable tools and sources you are authorized to access. These are options, not a mandatory checklist. Ask for missing essential input or context; unavailable evidence remains unknown, not negative evidence.

- Record Snapshots & Exports for the visible issue set, impact, deadlines, commitments and evidenced response-time state.
- Email & Interaction Notes for repeated unanswered contact and substantive customer urgency.
- Internal Messaging for evidenced blocked dependencies and escalation context, not a reason to demote urgency.
- Knowledge & Files for supplied priority, weighting and tie-break rules within their effective scope.

Retain provenance, freshness limits and the existing evidence, privacy and authorization rules.

## Purpose
Produce an explainable relative work order: what should be handled first, why it outranks
the alternatives, which evidence drove the judgment, and what uncertainty could change
the order.

## Applicability
Comparative ranking requires at least two issues with enough evidence to distinguish their
relative urgency. A single issue can receive a bounded urgency assessment, but it cannot be
given a fictitious rank within an unseen queue.

Response-time targets and priority fields are useful evidence, not prerequisites. Impact,
hard deadlines, customer commitments, staleness, repeated unanswered contact, and
documented urgency can support prioritization when those fields are absent.

## Usage situations
- "Rank these issues and show which one should be first."
- "Rank these requests and explain the order."
- "Which complaints need attention today?"
- "How urgent does this one issue appear?"
- "Show why the first item outranks the second."

## Procedure
1. Define the issue set and effective scope being ranked.
2. Normalize the available evidence for each issue without treating absent fields as
   negative facts.
3. Identify hard constraints first: confirmed breaches, explicit deadlines, severe impact,
   and commitments that are due or overdue.
4. Assess remaining urgency using customer impact, repeated unanswered contact, staleness,
   documented priority, and credible escalation evidence.
5. Apply supplied organizational weighting and tie-break rules. Without them, use a
   conservative qualitative comparison and explain the trade-offs.
6. If two or more issues remain in scope, rank them and state "why now" and "why ahead of
   the next item" for the leading candidates. If only one issue remains in scope, produce a
   bounded urgency and evidence assessment for it and assign no queue rank.
7. For each leading item, state whether it calls for immediate handling, a dependency
   follow-up (the next step is blocked on another party or system), or escalation. An
   urgent issue blocked on a dependency keeps its rank and urgency signal; do not lower
   either merely because a less urgent issue is immediately actionable.
8. Identify missing, conflicting, or stale evidence that could materially change the
   order and recommend the narrowest follow-up.

## Judgment
- Distinguish a confirmed response-time breach from inferred urgency. Age, tone, or stated
  importance alone does not prove a breach.
- Do not prioritize by raw complaint count alone. Repeated contact matters when it
  indicates unresolved impact, a missed commitment, or sustained lack of response.
- Keep unknown fields unknown. A missing priority, deadline, or timer is not "low," "none,"
  or "on track."
- Apply organization criteria only within their stated scope and effective period.
- Do not invent scores, confidence values, weights, service thresholds, or tie-break rules.
- Actionability (immediate handling, dependency follow-up, or escalation) is separate from
  urgency. A high-urgency issue blocked on a dependency is not demoted by a lower-urgency
  issue that happens to be actionable right now; report both facts side by side.
- Rank strictly on the evidence in Procedure steps 3-5. Do not import revenue, deal size, or
  other commercial weighting into this ranking.

## Output

For comparative triage, deliver two parts: one concise chat summary and one saved primary editable artifact containing the complete triage result. The chat summary does not replace the saved artifact. For one issue, keep the bounded urgency assessment in chat by default; create and save an artifact only when requested.

### Chat summary

In chat, name the top supported item or urgency band, the factor that most changed the ordering, the largest coverage or evidence gap, and the immediate next action. State whether the result ranks a complete population or only a bounded visible set.

### Artifact content

For comparative triage:
- The ranked worklist and effective scope.
- Evidence-based rationale for each leading item.
- Confirmed versus inferred urgency.
- Actionability for each leading item: immediate handling, dependency follow-up, or
  escalation.
- Material unknowns, conflicts, or stale evidence.
- The recommended first item and narrowest next action.

For one issue, return an urgency assessment and comparison-ready evidence summary without
assigning a queue rank.

For comparative triage, use one row per evaluated issue with columns for evidence-based
urgency factors, unknowns, ordering rationale, and proposed next action. Record population
boundary, filters, caps, evidence cutoff, calculation logic if any, source references, and
validation outcome.

### Artifact selection

Choose the format for the complete triage result, respecting the user's requested format and the single-issue chat default:

- **Excel (.xlsx):** Default for comparative triage with filterable ordering, urgency evidence and actionability.
- **Word (.docx):** For a requested review document or warranted escalation handoff; add an escalation brief only when a few issues need narrative handoff or executive review. A single-issue durable brief requires a request.
- **Markdown (.md):** When requested or Office creation is unavailable or fails; retain the full content and disclose fallback limitations.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

For comparative triage, create and save the complete triage result in the selected format as the primary editable review artifact.

Verify each save before reporting success and provide the actual link or location. If saving fails, disclose it and provide clearly labeled unsaved triage in chat.

## Guardrails
Creating and saving the requested file artifact in an authorized location is permitted.
Ranking is otherwise read-only. It does not claim, assign, update, or escalate work. Each such effect
requires applicable internal authority and explicit approval for the specific issue and
action. Report recommendations, approvals, completed effects, and unconfirmed effects
separately.

## When NOT to Use
- Not for a deep brief on one selected issue; use `case-preparation-brief`.
- Not for a one-item next-work recommendation or a resolve-and-next transition when the user
  does not need an ordered triage view; that requires a separate authorized case-resolution workflow outside this catalog.
- Not for automatically assigning, claiming, updating, or escalating work.
- Do not present a ranking over a partial or hidden queue as though it covers all work.

## Required information
- **Ranking baseline:** at least two issues and some comparable evidence about impact,
  deadlines, commitments, age, contact history, priority, or response-time state.
- **Single-issue baseline:** one issue with enough evidence for a bounded urgency
  assessment.
- **Broader scope:** fuller histories, organizational criteria, ownership context, and
  response-time evidence improve precision without changing the procedure.
