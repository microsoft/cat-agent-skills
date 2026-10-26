---
name: incident-writeup
description: Drafts the incident summary and the root-cause-analysis (RCA) template from the assembled contract payload, with every determination cited to OSHA, ISO 45001, the JHA and internal policy. Use when the user says "draft the incident summary", "write up the incident", "give me the RCA template", "prepare the OSHA writeup", or after routing-notify completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: EHS
---

# Incident Write-up

## Purpose
Produce the human-readable artifact: an incident write-up rendered from
`templates/incident-writeup-template.md`, populated only from the contract payload — the incident
context, the classification (severity, recordable + column, reportable + clock), the routing and
notifications, the reporting checklist, the recommended next-best action, and a root-cause-analysis
template (5-Why; fishbone for high/critical).

## When to use
- After routing-notify, to close the loop.
- "Draft the incident summary" / "give me the RCA template" / "prepare the OSHA write-up".

## Inputs
- `incident-packet.json` (contract `mfg.safety-incident-assist.v1`, the `{routing}` hop with
  `classification{}`, `routing{}`, `next_best_action`, `escalations[]`).

## Steps
1. Validate input against the contract.
2. Fill `templates/incident-writeup-template.md`: incident identification, factual summary, the
   classification block, the routing & notification list, the regulatory clock, a visible "Open
   items / escalations" block, the recommended next-best action, and the RCA template
   (`references/rca-standards-excerpts.md` #4).
3. Render to the requested format (markdown; DOCX/PDF via the platform document component).
4. Choose the audience voice: EHS manager, line supervisor, or plant manager.
5. Mark the write-up DRAFT — pending EHS-owner review and sign-off.

## Output
`INC-<incident_id>-writeup.md` (or .docx) — the terminal artifact of the contract flow.

## Grounding requirements
The classification traces to `engine:recordability_classify`; the routing traces to
`engine:routing_notify`; OSHA/ISO/JHA references cite the reference files.

## Constraints
- Draft-first: no OSHA filing, no auto-notification, and no incident closure in v1. The write-up is
  a recommendation, not an executed action — this preserves the reporting checklist and audit trail.
- Nothing appears in the write-up that is not present in the contract payload.
- A recordable/reportable determination and its regulatory clock must never be softened or hidden in
  the draft.

## Escalation / uncertainty
- If `escalations[]` is non-empty, the write-up must surface them in a visible "Open items /
  escalations" block above the recommended action — especially a reportable clock, a recordable
  entry, or a repeat pattern.
