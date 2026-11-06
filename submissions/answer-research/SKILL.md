---
name: answer-research
description: Researches a bounded, source-backed answer to a support, policy, eligibility, or troubleshooting question, with citations and explicit evidence gaps. Use when a support, policy, eligibility, informational, or troubleshooting question needs a bounded, source-backed investigation that reconciles authority, applicability, currency, contradictions, and source coverage. Triggers include "research this answer," "what does the guidance support," "reconcile these sources," and "does this customer appear eligible." Do not use merely to compose a reply after the answer is established.
metadata:
  displayname: Answer Research
---

# Answer Research

Domain: Customer Service.

Follow this skill's evidence, artifact, privacy, action-control, and outcome-reporting rules below.

## Evidence and connectivity

Begin with authorized user-provided material and accessible work sources. Discover optional CRM, knowledge, communication, quality, and workflow capabilities at runtime and use them only to enrich or execute the job; never require a vendor, connector, record identifier, object name, or field name when the minimum semantic evidence is otherwise available.

If a capability is unconfigured, unavailable, denied, stale, partial, or unsupported, continue with the supported baseline, disclose the affected scope, and block only the dependent conclusion or action. Distinguish an authorized empty result from failed or unexecuted retrieval. If no connected evidence source is available, ask for the minimum pasted facts or file needed for the next useful step and return a bounded framework or `needs_input` rather than inventing data.
Use supplied material and authorized knowledge, policy, issue, correspondence, and attachment sources that can answer the resolved question. Search or connected CRM access is optional enrichment. Preserve authority, applicability, effective date, source coverage, contradictions, and the difference between no matching evidence and failed retrieval.

## Data Sources

Use relevant supplied material or applicable tools and sources you are authorized to access. These are options, not a mandatory checklist. Ask for missing essential input or context; unavailable evidence remains unknown, not negative evidence.

- Knowledge & Files for governing policies, articles, effective dates, exceptions and source-authority rules.
- Record Snapshots & Exports for customer or issue facts needed to test the applicable criterion.
- Email & Attachments for the actual question, customer-provided evidence and material contradictions.
- Public official guidance for applicable product or policy facts absent internally, without assuming it overrides governing internal sources.

Never send confidential content to public search. Preserve source authority, dates and privacy boundaries.

## Purpose
Produce a bounded, source-backed answer to a specific question. Plan the investigation,
reconcile the available evidence, explain how it applies to the customer or issue, and
state both covered and missing source areas.

## Applicability
Applies when there is a specific question and at least one relevant source, excerpt,
record, correspondence item, policy, article, or other piece of material to analyze. A
searchable collection is useful but not required. Material already present can support a
bounded finding.

A request for "all" relevant guidance requires known source coverage. When coverage is
unknown or incomplete, report the bounded coverage rather than implying an exhaustive
answer.

## Usage situations
- "Research the answer to this customer's question."
- "What does the supplied policy support?"
- "Reconcile these two articles."
- "Does this customer appear eligible under the available guidance?"
- "Find the gaps before this answer is used in a reply."

## Procedure
1. Frame the primary question and the subquestions needed to answer it.
2. Identify which source categories could materially affect the answer and classify each
   as covered, unavailable, or not checked.
3. Review the available material for direct answers, qualifying conditions, exceptions,
   effective scope, and customer-specific facts.
4. Assess each relevant source for authority, applicability, currency, and completeness.
5. Reconcile consistent, partial, and conflicting evidence. Prefer authoritative, applicable policy over text that is merely newer. Before summing amounts, establish distinct transactions and compatible customer/account identity, units or currency, and time scope. Conflicting accounts of one event remain alternatives, not amounts to add; when unresolved, report the alternatives and missing evidence.
6. Before stating a policy or eligibility determination, establish the applicable governing criterion and a compatible set of facts that satisfies it. If either is unresolved, lead with the unresolved determination and the missing dependency, then give the supported findings. Do not lead with a definitive branch and weaken it only in a later caveat. Label precautionary advice separately from a policy finding.
7. State source coverage, citations, missing areas, conflicts, stale evidence, unsupported
   subquestions, and the narrowest useful next research step.

## Judgment
- **Authority:** apply supplied source hierarchy or governance rules. Without them,
  describe competing authority signals rather than inventing a winner.
- **Applicability:** distinguish a general rule from evidence that it applies to the
  customer, product, date, location, or issue.
- **Currency:** use effective dates and supersession evidence. Newer wording does not
  automatically override an older governing source.
- **Evidence states:** keep missing, negative, conflicting, and stale evidence distinct. A
  failed search is not proof that no guidance exists.
- **Policy and eligibility:** do not convert an inference into a policy, entitlement, or eligibility fact. If the governing rule or threshold cannot be established, leave the dependent determination open. Do not substitute a remembered general rule or a rule for a different activity; report the supported facts and the exact missing criterion.

## Output

Deliver two parts: one concise chat summary and one saved primary editable artifact containing the complete internal answer-research brief. The chat summary does not replace the saved artifact.

### Chat summary

In chat, state the supported answer, strongest applicable authority, largest unresolved conflict or source gap, and the next validation or service action. Do not lead with search mechanics or source volume.

### Artifact content

- The question and any material subquestions.
- The supported answer, with citations to sources actually reviewed. For a policy or eligibility question, lead with the determination's status and governing criterion; an unestablished criterion leaves the dependent determination unresolved.
- How the evidence applies to the customer or issue.
- Sources and source categories covered.
- Missing, conflicting, or stale evidence.
- Any unsupported conclusion and the recommended next research step.

If only part of the question is supported, return that part and identify the unanswered
subquestions. A bounded finding is a complete result when the limits are explicit.

Identify audience, purpose, question, evidence cutoff, source coverage, assumptions, limitations, claim-to-source references, and validation outcome. Do not create a customer reply unless separately requested.

### Artifact selection

Choose the format for the complete internal answer-research brief, respecting the user's requested format:

- **Word (.docx):** Default for reviewing the answer, governing criterion, reasoning and limitations together.
- **Excel (.xlsx):** Add a source matrix only when comparison by authority, applicability, date or conflicting claim materially helps.
- **Markdown (.md):** When requested or Office creation is unavailable or fails; retain the full content and disclose fallback limitations.

Use authorized, format-specific workflows. Keep content concise and styling simple. Plan changes together and apply them in as few supported batches as practical. Update authorized existing artifacts without creating duplicates or changing unrelated content. Follow Delivery and control for saving and reporting.

### Delivery and control

Create and save the complete internal answer-research brief in the selected format as the primary editable review artifact.

Verify each save before reporting success and provide the actual link or location. If saving fails, disclose it and provide clearly labeled unsaved research in chat.

## Guardrails
Creating and saving the requested file artifact in an authorized location is permitted.
Research is otherwise read-only analysis. It does not authorize a record change, customer
commitment, eligibility decision, or outbound communication. Report proposed, approved,
completed, and unconfirmed outcomes separately.

## When NOT to Use
- Not for general research without a support question.
- Not for composing the outward-facing reply after the answer is established; use `draft-customer-reply`.
- Not for turning a resolved issue into reusable guidance; use `knowledge-harvest`.
- Do not invent citations or claim exhaustive coverage when the available collection is
  unknown.

## Required information
- **Baseline:** the question and relevant material sufficient to investigate at least one
  material part of it.
- **Broader scope:** additional governed sources, customer facts, source metadata, and
  known collection coverage deepen the same investigation. Their absence narrows the
  finding rather than preventing analysis of material already available.
