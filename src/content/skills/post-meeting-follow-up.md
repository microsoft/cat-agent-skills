---
name: Post-Meeting Follow-Up
description: "Capture sales meeting decisions and commitments, propose next actions, and draft a reviewable customer follow-up."
agentDescription: "Turns one completed sales meeting into an accurate summary of decisions and commitments, proposed next actions, and an optional customer follow-up draft. Use when one completed sales meeting or call needs accurate capture, proposed durable actions, and safe customer follow-up, such as \"summarize this completed call\", \"capture meeting commitments\", or \"draft the meeting follow-up\". DO NOT use for upcoming meeting prep, account-wide activity summaries, or lead re-engagement campaigns."
platforms: [Cowork]
category: sales
builtByMicrosoft: true
tags: [sales, meetings, follow-up]
author: Copilot Cowork team
authorUrl: "https://www.microsoft.com/en-us/copilot/features/cowork"
createdAt: 2026-10-31
---
# Post-Meeting Follow-Up

Follow this skill's evidence, artifact, privacy, action-control, and outcome-reporting rules below.

Domain: Sales.
## Evidence and connectivity

Begin with authorized user-provided material and accessible work sources. Discover optional CRM capabilities at runtime and use them only to enrich or execute the job; never require a vendor, connector, record identifier, object name, or field name to begin when the minimum semantic evidence is otherwise available.

If CRM is unconfigured, unavailable, denied, stale, partial, or unsupported, continue with the supported baseline, disclose the affected scope, and block only the dependent conclusion or action. Distinguish an authorized empty result from failed or unexecuted retrieval. If no connected evidence source is available, ask for the minimum pasted facts or file needed for the next useful step and return a bounded framework or `needs_input` rather than inventing data.

## Data Sources

Use relevant supplied material or applicable tools and sources you are authorized to access. These are options, not a mandatory checklist. Ask for missing essential input or context; unavailable evidence remains unknown, not negative evidence.

- Meeting Transcripts & Notes for the completed interaction, explicit decisions and accepted commitments.
- Email for corroborating agreed dates, subsequent clarifications and permitted follow-up context.
- Record Snapshots & Exports for current values against which proposed durable changes can be verified.
- Knowledge & Files for supplied stage, forecast, recordkeeping and communication-policy rules.

Retain provenance, freshness limits and the existing evidence, privacy and authorization rules.

## Purpose
Turn one completed meeting into an accurate summary, durable record implications, proposed
next actions, and an optional communication draft without treating discussion as agreement
or a draft as sent.

## Applicability
Use this procedure when one completed meeting or call has substantive evidence in notes, a
transcript, or another communication record. Current record state is optional. Its absence
does not block a summary or draft, but record-field changes remain unverified proposals.

## Usage situations
- "Turn these meeting notes into a follow-up package."
- "Summarize decisions and commitments and draft the customer follow-up."
- "What should be recorded or done after this call?"
- Non-trigger: "Summarize everything that has happened with this account."

## Procedure
1. Resolve the completed meeting from an explicit user reference, supplied evidence, or
   trusted selected-meeting/conversation context. An unspecified "that call" is not resolved
   by choosing the latest visible event. If unresolved, ask one focused question identifying
   the meeting or requesting its notes before extracting agreements or preparing a
   meeting-specific package. Once resolved, establish participants, date, related business
   context, and evidence scope. Resolve any related record separately; ambiguity there blocks
   only record-specific proposals or actions, not a supported summary or draft.
2. Extract and distinguish:
   - **Facts:** directly supported by the meeting evidence.
   - **Decisions:** options explicitly selected.
   - **Commitments:** actions or outcomes explicitly accepted by a party.
   - **Open topics:** questions or possibilities discussed without agreement.
3. Preserve source/date for commitments, owners, and deadlines. Retain contradictions
   when the evidence does not resolve them.
   Use one resolved date and timezone for each event or deadline; derive any weekday label from that date. Preserve requested, proposed and accepted dates separately.
4. Compare durable implications with current context when available. Without current
   state, label field and stage changes as unverified proposals.
5. Apply supplied organization rules for stage, forecast, next action, and recordkeeping.
   Do not infer stage progression merely because a stage-related topic was discussed.
6. Propose the meeting note, exact record deltas, next actions, owners, and dates.
   Tie a commercial field proposal to an explicit commercial decision or commitment. A pilot duration alone does not establish a close date, stage or forecast change. Show an unavailable current value as unknown, not an inferred old value or a verified delta. Retain supported notes and task proposals independently of blocked commercial changes.
   Keep conditional plans conditional; signing after a successful pilot is not an unconditional
   signing date. Retain the condition in summaries and proposals, and flag any commercial
   delta whose basis still needs confirmation.
7. When requested, draft customer communication using only supported facts and
   commitments. Keep it explicitly in draft state.
8. Present each proposed write, send, assignment, schedule, or commitment separately.
9. Resolve the target and evidentiary basis before seeking execution approval. Do not invoke a
   business-record write, send, or scheduling tool to obtain approval while the target or
   change basis remains unresolved. If execution is requested, carry out only specifically
   approved actions and verify each result.

## Judgment
- Silence or lack of objection is not consent.
- A meeting can justify a note or task while remaining insufficient for a commercial
  field, forecast, close date, or stage change.
- Direct statements outweigh inference; current authoritative evidence outweighs stale
  context unless an applicable rule says otherwise.
- Missing, negative, stale, conflicting, and inaccessible evidence remain distinct.
- Do not invent participants, owners, deadlines, outcomes, stage rules, or commitments.

## Output

Deliver both a concise chat summary and one saved primary editable artifact, following the
sections below. The artifact must contain the meeting capture or seller requested customer-only
follow-up draft.

### Chat summary

In chat, summarize the most important decision or outcome, the highest-priority commitment, the
largest unresolved attribution or agreement gap, and the next follow-up action. Clearly label
the customer communication as a draft and state whether any record implications remain
unverified proposals.

### Artifact content

Provide:
- concise meeting summary;
- facts and decisions;
- commitments with owners and dates;
- open questions and contradictions;
- proposed durable record implications;
- proposed next actions;
- customer communication draft when requested;
- action state for every consequential item: proposed, approved, completed, or
  unconfirmed.

A summary and draft proposal are complete useful outputs even when no record snapshot or
execution path is available.

Keep internal negotiation guidance, record implications, restrictions, and evidence gaps in
chat or a separate internal artifact, never in the customer-ready draft.

## Artifact selection

Choose the format for complete meeting capture and follow-up, respecting the user's requested format and the required audience separation:

- **Word (.docx):** Default; customer-only draft when communication is requested, otherwise one complete internal capture package.
- **Excel (.xlsx):** An internal register for many owners, dates, dependencies or approvals; replace the internal package or accompany the customer draft.
- **Markdown (.md):** When requested or Office fails; retain complete audience-separated content and disclose lost register functionality.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Verify each save before reporting success and provide the actual links or locations. If saving fails, disclose it and provide clearly labeled, audience-separated unsaved content in chat. Keep customer drafts message-like and internal registers tabular; a saved draft is not a sent follow-up.

## Guardrails
Creating and saving the requested file artifact in an authorized location is permitted.
Summarizing, drafting, and recommending do not authorize a business-record note, field change, stage move,
task, meeting, assignment, send, or commitment. Each action requires explicit approval of
the exact content, target, recipients, and timing as applicable. Approval to save a business-record note
does not authorize a message or stage change. Organization authority and execution
approval remain separate. Before sending the customer communication draft, recheck the
applicable contact-policy and consent restriction for that recipient and channel; the
operator's approval to send and the recipient's contact permission are separate, and an
unresolved required permission blocks the send. Verify before reporting completion.

## When NOT to Use
- Not for upcoming meeting preparation; use `meeting-prep`.
- Not for a broad relationship history or a full work period across records; use a separate
  activity-synthesis procedure outside this catalog.
- Not for selecting who to engage across an account; use a separate engagement-planning procedure outside this catalog.
- Do not invent meeting content, infer agreement from discussion, or treat a draft as sent.

## Required information
- **Minimum:** one completed meeting and substantive notes, transcript, or communication
  evidence.
- **Optional enrichment:** participant and record context, current record state, prior
  commitments, and organization stage or follow-up rules. Missing current state limits
  verified deltas but does not block summary or drafting.
- **Missing-input question:** "Which meeting, or can you share the notes?"
