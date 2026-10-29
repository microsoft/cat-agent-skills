---
name: necessity-draft
description: "Writes the medical-necessity narrative that accompanies a pending prior-auth request, using only criteria the engine marked met and cited. Use when the user says \"write the medical-necessity letter for this MRI request\", \"draft the clinical justification for the auth\", \"explain to the plan why this procedure is needed\", \"put together the necessity narrative\". Do NOT use to list what is still missing or check packet readiness - use gap-report instead; do NOT use to decide whether the criteria are met - use criteria-extract instead; do NOT use to argue against a decision the payer has already made - use the denials-appeals-response plugin instead. Never writes approval, denial or clearance language."
license: MIT
metadata: {version: "1.0.3", author: Microsoft Healthcare & Life Sciences Skills, category: analysis, domain: "Prior Authorisation", action_level: "L1", risk: "high", icon: Compose}
---
# Necessity Draft
## Purpose
Produce the draft narrative text that accompanies the authorisation request, for clinician review.

## When to Use
- After criteria-extract, whenever `criteria_met` is non-empty and the user asks for the justification, letter or narrative for a pending request.

## When NOT to Use
- `criteria_met` is empty or determination is out_of_scope - use gap-report instead.
- The user wants the gaps listed or asks whether the packet is ready - use gap-report instead.
- The user wants the evidence located - use evidence-match instead.
- The payer has already issued a denial and the user wants it appealed - use the denials-appeals-response plugin instead.
- The user asks for narrative covering a criterion that is still in gaps - that part is declined, not softened.

## Inputs
`criteria_result` (criteria_met with citations, gaps); `request{service, payer, clause}`; `necessity_narrative`
if a prior draft exists.

## Workflow
1. Read `criteria_result.criteria_met` from the engine output (tool: `python3 base/scripts/criteria_engine.py --question <contract.json> --policy config/payer-policy-library.json --out <contract.out.json>`, run by criteria-extract) and take each entry with its citation.
2. Write the first line exactly: `DRAFT - for clinician review before any request is sent.`
3. Write one opening sentence: `This narrative accompanies a request to <payer> for <service> under policy clause <clause>.` - no coverage conclusion, and never "submitted" (nothing has been sent).
4. Write one paragraph per met criterion using the template `<criterion text>: the <source_note> dated <note_date> records "<quote>".` Add nothing that is not in the quote.
5. Skip every criterion in gaps - name nothing, imply nothing, do not narrate around the absence. If the user asked for it, add one decline line and route it to gap-report as a named gap.
6. Write `necessity_narrative` to the contract as draft text; scan it for the prior-auth-rules.md #2a tokens and rewrite any sentence that contains one.

## Output Format
`necessity_narrative` - a plain-text string on the contract: the DRAFT line, the opening sentence, then one
paragraph per met criterion in the fixed template above. No section headings, no bullet lists, no determination
language, no signature block. Any decline is a separate line after the narrative, never inside it.

## Example
```
DRAFT - for clinician review before any request is sent.
This narrative accompanies a request to Contoso Health Plan for mri_lumbar_spine under policy clause RAD-7.2.

No red-flag findings (cauda equina, progressive neuro deficit, suspected malignancy/infection): the Spine clinic intake note dated 2026-09-12 records "No red-flag findings on review of systems".

Focal neurological exam findings consistent with radiculopathy documented: the Spine clinic intake note dated 2026-09-12 records "Positive straight-leg raise on the left, reproducible radicular pain".

Declined: conservative_therapy_6wk is an open gap (reason no_evidence, RAD-7.2) and is not narrated; routed to gap-report.
```

## Grounding requirements
Every sentence in the narrative traces to a `criteria_met` entry and its citation. No clinical detail, severity,
duration, failed-therapy history or exam finding may appear unless it is in a cited quote - persuasive-sounding
filler in a medical-necessity letter is a compliance risk, not a stylistic choice. If a paragraph cannot be written
from cited evidence, it is not written.

## Guardrails
- Action level L1 (draft only): produces text for a human to review; it sends, emails or uploads nothing.
- Never narrate a criterion that is in gaps as though it were met.
- Never draft language implying approval, denial or clearance - this is a request narrative only (prior-auth-rules.md #2).
- Never overstate duration, frequency or severity beyond what the cited quote states.
- Never strip or weaken the draft marking on the narrative or the packet to make it look final.
- Always leave review and sending to the clinical reviewer role (`config/escalation-contacts.json`).

## Error Handling
- If `criteria_met` is empty, or determination is out_of_scope: produce no narrative and defer entirely to gap-report.
- If asked to include an unevidenced criterion: decline in writing and route it to gap-report as a named gap.
- If a met entry is missing its quote: do not paraphrase from memory; hand back to evidence-match.
- If asked to send the narrative to the payer: decline; the plugin has no send action.
