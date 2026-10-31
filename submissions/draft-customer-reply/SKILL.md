---
name: draft-customer-reply
description: Drafts a reviewable customer-facing support reply grounded in known facts, applicable policy, and the customer's actual needs. Use when a ticket, incident, issue, request, or complaint needs a reviewable customer-facing reply grounded in the known facts, applicable policy, customer need, and communication context. Triggers include "draft a reply," "respond to the customer," "write a status update," and requests to adjust tone, length, or language. Do not use to research an unresolved answer or to send automatically.
metadata:
  displayname: Draft Customer Reply
---

# Draft Customer Reply

Domain: Customer Service.

Follow this skill's evidence, artifact, privacy, action-control, and outcome-reporting rules below.

## Evidence and connectivity

Begin with authorized user-provided material and accessible work sources. Discover optional CRM, knowledge, communication, quality, and workflow capabilities at runtime and use them only to enrich or execute the job; never require a vendor, connector, record identifier, object name, or field name when the minimum semantic evidence is otherwise available.

If a capability is unconfigured, unavailable, denied, stale, partial, or unsupported, continue with the supported baseline, disclose the affected scope, and block only the dependent conclusion or action. Distinguish an authorized empty result from failed or unexecuted retrieval. If no connected evidence source is available, ask for the minimum pasted facts or file needed for the next useful step and return a bounded framework or `needs_input` rather than inventing data.
Use supplied material and authorized issue, interaction, policy, knowledge, attachment, and fulfillment evidence needed for the reply. Connected CRM and communication systems are optional enrichment. Separate verified facts, customer statements, approved policy language, proposed commitments, and unknowns before drafting.

## Data Sources

Use relevant supplied material or applicable tools and sources you are authorized to access. These are options, not a mandatory checklist. Ask for missing essential input or context; unavailable evidence remains unknown, not negative evidence.

- Email & Interaction Records for the customer's actual need, prior messages and intended recipient or thread.
- Record Snapshots & Exports for verified issue facts, fulfillment results and remedy state.
- Knowledge & Files for established answers, approved policy language, attachments and applicable communication constraints.
- Supplied Preferences for the customer's language and the requested tone or length, without inventing facts.

Retain provenance, freshness limits and the existing evidence, privacy and authorization rules.

## Purpose
Produce a reviewable customer-facing draft that answers the customer's actual need with
the right policy basis, completeness, tone, language, and privacy treatment.

## Applicability
Applies when the customer need and enough supporting evidence are known to draft a useful
response. The evidence may be a message, issue description, interaction history, verified
answer, or applicable policy. A saved email record or complete logged history is not
required.

Thin evidence can support a bounded acknowledgment or request for information. It cannot
support invented facts, promises, compensation, deadlines, or resolution claims.

## Usage situations
- "Draft a response to this complaint."
- "Reply to the customer's last message."
- "Write a concise update in the customer's language."
- "Explain the verified resolution and next steps."
- "Make this draft warmer and shorter."

## Procedure
1. Identify the customer need, intended recipient, communication channel, and purpose.
2. Assemble the facts, commitments, applicable policy, and prior communications that
   materially constrain the response.
3. Separate verified outcomes from attempted or proposed remedies and identify answer gaps.
4. Decide whether the response should provide a direct answer, acknowledgment, request for
   information, status update, next steps, or verified resolution.
5. Draft in an appropriate tone, length, and language while excluding unnecessary personal,
   confidential, and internal information.
6. Check policy correctness, answer completeness, promise language, dates, compensation,
   recipients, and privacy.
7. Present the draft with unresolved factual or approval dependencies. Stop before sending.

## Judgment
- **Correctness:** ground every factual, policy, eligibility, deadline, and remedy claim in
  available evidence.
- **Completeness:** answer each material customer question or identify it as unresolved.
  Empathy does not substitute for an answer.
- **Remedy state:** distinguish attempted, proposed, approved, completed, and verified
  effective remedies.
- **Commitments:** do not promise timelines, compensation, exceptions, or outcomes without
  evidence of the relevant authority and agreement.
- **Privacy:** include only information appropriate for the named recipient and channel.
- **Contradictions:** surface material conflicts in the grounding rather than silently
  selecting the most convenient version.

## Output

Deliver two parts: one concise chat summary and one saved primary editable artifact containing the complete customer-only reply draft. The chat summary does not replace the saved artifact. When the user requests an email or CRM draft, use that saved native draft as the primary artifact rather than creating an additional Word file.

### Chat summary

In chat, summarize the reply purpose, recommended message posture, the most important fact or commitment requiring validation, and the next review or send decision. Do not expose internal rationale, permission findings, or policy deliberation in the customer-ready text.

### Artifact content

- A reviewable subject or opening and message body.
- Any evidence-dependent caveat that should remain visible.
- Any factual, policy, privacy, or approval item that must be resolved before sending.

A bounded acknowledgment or information request is useful when a full answer is not yet
supported. Do not present it as a complete resolution response.

Include only the customer-appropriate subject or opening and message body in the draft;
recipient, channel, purpose, and language may be represented as customer-safe document metadata
when useful. Keep the evidence
cutoff, unresolved approvals or fact checks, source references, and validation outcome in the
chat run report or a separately identified internal note when requested; never mix them into the
customer copy. Do not claim that the reply was sent.

### Artifact selection

Choose one format for the complete customer-only reply draft, respecting the user's requested format:

- **Word (.docx):** Default for reviewing, editing and copying the subject or opening and full body into the intended channel.
- **Markdown (.md):** When requested or Word creation or saving fails; keep the message customer-only and disclose fallback outside it.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Create and save the customer-only reply draft as the primary editable review artifact. When the user specifies an email or CRM draft, create or update it on that surface instead of substituting a separate file.

Verify the save before reporting success and provide the actual link or location. If saving fails, disclose it outside the customer-only draft and provide clearly labeled unsaved reply text in chat. A saved draft is not a sent reply.

## Guardrails
Creating and saving the requested file artifact in an authorized location is permitted.
Drafting does not require send approval because it sends no communication. Sending
requires applicable authorization and explicit approval of the final recipients,
channel/thread, subject, and body, plus a recheck — at the moment of sending — of the
message's purpose and any applicable contact or communication policy for that recipient
and channel. Operator approval to send is separate from the recipient's own contact
permission: an unresolved required permission blocks sending, but a support reply does not
need marketing-style opt-in consent by default — apply whichever policy is actually in
force rather than inventing one. A substantive change after approval requires renewed
approval. A drafted or saved message is not a sent message; when sending is not permitted
or the applicable policy cannot be confirmed, keep the draft available for review rather
than withholding it.

## When NOT to Use
- Not for researching an unresolved policy or factual answer; use `answer-research`.
- Not for closing the underlying issue.
- Do not send automatically or imply delivery without confirmation.

## Required information
- **Baseline:** the customer need and enough issue evidence to support the intended
  message.
- **Broader scope:** fuller history, applicable policy, recipient/thread details, language
  preference, and communication constraints improve precision without making a persisted
  record a prerequisite.
