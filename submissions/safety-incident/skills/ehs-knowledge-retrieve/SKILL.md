---
name: ehs-knowledge-retrieve
description: Retrieves the OSHA recordability criteria, ISO 45001 clauses, JHA/HIRA and internal EHS policy relevant to an incident and attaches them plus prior similar incidents to the mfg.safety-incident-assist.v1 contract. Use when the user says "pull the OSHA criteria", "get the JHA for this task", "have we had this incident before", "what does policy say", or after incident-intake completes.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: EHS
---

# EHS Knowledge Retrieve

## Purpose
Enrich the incident payload with grounded knowledge: the applicable OSHA 300/300A recordability
criteria, the relevant ISO 45001 clauses, the JHA/HIRA for the task/area, internal EHS policy, and
the area's prior similar incidents (to reveal a repeat pattern).

## When to use
- After incident-intake, in every run.
- "Pull the OSHA criteria and the JHA" / "have we had this incident on this machine before?".

## Inputs
- `incident-intake.json` (contract inputs from incident-intake).
- OSHA recordability excerpt, JHA/HIRA excerpt, EHS policy excerpt (PDF/Markdown).
- Prior-incident log (CSV): incident_id, date, area, asset_or_area, type, body_part, outcome,
  recordable.

## Steps
1. Filter the prior-incident log to this `asset_or_area` (and body_part/type where relevant); extract
   each into `history.prior_incidents[]` with its `outcome` and `recordable` flag.
2. Set `history.window_days` to the span covered and compute `history.repeat_count`. Set
   `history.repeat_pattern = true` when the same area/asset shows recurring similar incidents
   (a systemic signal, `ehs-policy-excerpts.md` #4).
3. Attach retrieved OSHA criteria, ISO 45001 clauses, JHA/HIRA and policy excerpts into
   `retrieved{}`, each with a citation.
4. Write the enriched payload back onto the contract.

## Output
The contract payload with populated `history{}` and `retrieved{}` — the input to
severity-recordability.

## Grounding requirements
Every prior incident cites its log record ID; every criteria/clause/JHA reference cites its section
or file.

## Constraints
- Retrieval only — do not classify severity or recordability here (engine/LLM split).
- Do not infer a prior incident's recordability if the log does not state it.
- Do not drop a prior incident that reveals a repeat pattern; surfacing it is the point.

## Escalation / uncertainty
- If the prior-incident log or JHA is unavailable, proceed on the report and OSHA criteria alone and
  note it in `escalations[]`; do not block the run.
