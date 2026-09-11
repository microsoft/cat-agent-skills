---
name: evidence-gather
description: Builds the evidence register for the mapped clauses from the uploaded QMS exports and document indexes. Use when the user says "gather the evidence", "what do we have on file", "build the evidence register", or after scope-map in a readiness run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# Evidence Gather
## Purpose
Assemble the register the Govern engine validates: every candidate evidence item with type, date, area, person, and source identity.
## When to use
After scope-map in every run.
## Inputs
mapped.json; uploaded evidence indexes/exports (CSV/JSON/folder listings of minutes, audit reports, training records, calibration logs, NCR logs).
## Steps
1. For each required evidence type, list the items on file: type, date, area, person, doc id.
2. Record dates exactly as documented - freshness is the engine's call, not this skill's.
3. Write evidence.json.
## Output
evidence.json - the register.
## Grounding requirements
Every item cites its document id / export row.
## Constraints
- Gather only; no completeness or freshness judgments - "the folder looks full" is not a status.
- Never omit an item because it looks old; the engine needs it to prove staleness.
## Escalation / uncertainty
Evidence types with zero candidates are recorded as empty, not padded.
