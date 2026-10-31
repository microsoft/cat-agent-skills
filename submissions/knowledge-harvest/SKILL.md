---
name: knowledge-harvest
description: Helps customer service representatives harvest reusable knowledge from a recently closed case or verified workaround, with a brief chat summary and one saved editable review artifact in CRM when supported, otherwise in Word or Markdown. Separates symptoms, cause, workaround, fix, and tested scope, removes identifying details, checks guidance overlap, and proposes knowledge updates and recurrence-prevention actions without publishing. Use when asked to "capture a verified fix", "draft a knowledge article", "update an article from resolution evidence", or assess whether there is enough evidence for reusable guidance. Do not use to answer a current customer's question, draft their reply, turn unresolved speculation into executable instructions, or publish automatically.
metadata:
  displayname: Knowledge Harvest
---

# Knowledge Harvest for customer service representatives

Domain: Customer Service.

## Purpose

Help a customer service representative turn verified resolution evidence from a recently closed case into practical guidance for the next representative handling a similar issue. Separate the issue, cause, workaround, fix, scope, and caveats while removing customer-specific detail. The result is guidance for review and editing, not a published knowledge-base article.

## Applicability

Use when evidence supports a reusable lesson from a verified resolution or an observed workaround whose scope and verification limits can be stated.

Possible overlap with existing guidance does not automatically stop the task; an update or extension may be the better disposition.

If there is no verified reusable outcome, provide only a clearly labeled evidence-gap outline and the proof needed to complete it. Do not convert unresolved speculation into executable instructions.

## Data Sources

Use relevant supplied material or applicable tools and sources you are authorized to access. These are options, not a mandatory checklist. Ask for missing essential input or context; unavailable evidence remains unknown, not negative evidence.

- Resolution Notes for symptoms, investigation, attempted actions and observed outcomes.
- Verification Results for tested conditions, effectiveness and limits on generalization.
- Email for customer observations, later failures and recurrence reports.
- Meeting Transcripts for investigation decisions, scope clarifications and unresolved hypotheses.
- Internal Messaging for troubleshooting handoffs and verification caveats.
- Knowledge & Files for existing guidance, product or policy scope and overlap comparison.
- Support Records & Exports for the referenced issue's timeline, action history and affected environment.

Resolve the exact referenced context; do not assume a CRM connection. Request the missing evidence or exported case when needed.

## Usage situations

- "Turn this verified fix into reusable guidance."
- "Draft a knowledge article from these resolution notes."
- "Update the existing article with this newly verified caveat."
- "Capture this workaround but label what is not yet proven."
- "Is there enough evidence here for a reusable article?"

## Procedure

1. Assemble the available evidence: symptoms, investigation, attempted actions, observed outcomes, verification conditions, and applicable product or policy scope.
2. Separate observation, hypothesis, cause, workaround, fix, and verification. Confirm which action produced which observed result. A successful workaround does not necessarily prove root cause or a permanent fix.
3. Reconcile later failures or conflicting reports with earlier success. Limit a claim to the conditions and duration actually verified, or mark the outcome unresolved.
4. Determine what can be generalized and which product, version, environment, customer-segment, or policy conditions remain essential limitations.
5. Remove personal, customer-identifying, confidential, and irrelevant operational details from the reusable body. Keep any restricted source provenance separate and appropriate for the review audience.
6. Evaluate overlap with existing guidance and record comparison coverage. Distinguish full coverage of the verified lesson, partial overlap, and a missing new step or caveat. Leave unsupported overlap conclusions unresolved.
7. Choose a proposed disposition: new draft, update or extension, overlap/no-change note, or insufficient-evidence outline. Prefer an update when existing guidance already covers the issue but lacks a verified improvement.
8. Draft the title, audience/scope, symptoms, cause status, workaround or fix, prerequisites, ordered supported steps, expected result, verification method, caveats, and exclusions. Do not invent missing troubleshooting or product-operation steps to complete a template.
9. Save the reviewable draft and disposition with its source-evidence summary, overlap coverage, and unresolved verification or approval requirements in the final editable artifact, following the artifact-selection rules below.

## Judgment

- **Resolution sufficiency:** verification needs evidence of both action and outcome. Proposed, attempted, completed, and verified-effective actions are distinct. A closed status, generated summary, or statement that a fix was proposed does not establish that the action occurred and produced the claimed result.
- **Generalization:** include only steps and conditions justified by the evidence. One observed success does not establish universal applicability.
- **Cause versus remedy:** keep cause unknown when a successful workaround does not prove it.
- **Overlap:** a missing comparison corpus means unknown overlap, not a unique article. Finding similar guidance can support an update rather than automatic abandonment.
- **Conflicts and staleness:** prevent contradictory or superseded evidence from silently becoming reusable instructions.
- **Privacy:** remove customer names, contact details, identifiers, credentials, and restricted links that are unnecessary or inappropriate for the reusable audience. Do not invent provenance after de-identifying the content.

## Output
Provide one saved editable artifact following all above procedure and judgement. The artifact is the full knowledge harvest of following section:
- Proposed disposition and its rationale.
- Title and intended audience or scope.
- Issue or symptoms and cause evidence status.
- Workaround and fix, clearly distinguished.
- Prerequisites and ordered evidence-supported steps.
- Expected result, verification, and the conditions actually tested.
- Caveats, exclusions, source-evidence summary, and comparison coverage.
- Open facts or approvals kept separate from the reusable body.

When evidence is insufficient for a complete article, produce an evidence-gap outline that preserves verified facts and names the missing proof. Do not present it as ready-to-publish resolution guidance.
 
For an identified case with insufficient evidence, save a clearly labeled evidence-gap outline in the same structure and limit recommended actions to evidence collection and review. Do not present the outline as ready-to-publish resolution guidance.
 
**At the end of the chat session outside of the saved artifact, give a quick summary of the knowledge artifact generated. Do not include the full article, detailed research, or lengthy analysis in chat. Link to the saved artifact and identify any sections that deserve particular attention.**

 
### Artifact selection
 
Respect the requested format and destination; otherwise use the first supported option for the complete knowledge harvest:
 
- **CRM:** Discover suitable entities (for example, case notes or draft knowledge articles) and save tools in the underlying CRM at runtime. Save only when connected and a suitable editable entity and authorized write tool are available; otherwise continue with the file types below.
- **Word:** Default editable review draft when CRM saving is unavailable or fails.
- **Markdown:** When requested, or when Word is unavailable or fails.
 
Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.
 
## Delivery and control

Save the selected editable record or document and render it inline when supported. Respect tool permissions and confirmation requirements.

Keep the artifact in an authorized location for the intended review audience, and do not overwrite existing user content without specific authorization. Authorization to save the selected CRM review record applies only to the approved content, target, audience, and effect. Creating or saving a review artifact does not authorize sending, sharing, publishing, scheduling, commitments, consent changes, or other updates to underlying business records. Those actions require separate, specific authorization and approval of the exact content, target, audience, and effect. Recheck affected state and obtain renewed approval for material changes.

Verify saving and rendering separately before reporting success. Provide the actual CRM record link or identifier, or the file link or location; explain any CRM fallback. If rendering fails, disclose it and provide reviewable text. If no save succeeds, label that text unsaved. A saved artifact is not a sent message or another completed business action.

A Word or Markdown document or inline review draft is not a saved CRM record. A CRM case note or draft knowledge article is not published guidance. Keep knowledge articles in draft; do not overwrite published guidance. Discarding content or publishing remains a separately requested and approved action. Verify each actual effect; saving a review artifact never implies publication, and uncertain outcomes must be reconciled before retrying or creating a fallback artifact.

## Guardrails

Drafting requires no knowledge-authoring privilege. Creating and saving the requested file
artifact is permitted within authorized tools and locations. Saving a CRM or knowledge-record
draft, discarding content, and publishing are distinct consequential actions. Each requires
applicable authorization and explicit approval for the identified content and target.
Saving never implies publication, and no draft is published automatically.

## When NOT to Use

- Not for unresolved speculation except a clearly labeled evidence-gap outline.
- For an unresolved support answer, use `answer-research`; for a customer reply, use `draft-customer-reply`.
- Do not claim uniqueness without comparison evidence or publish automatically.
