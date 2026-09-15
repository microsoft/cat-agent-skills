---
name: ncr-intake
description: Reads the open NCR (the mfg.quality-inspection.v1 payload handed off by the Quality Inspection plugin), complaint log and inspection data into the mfg.quality-incident-capa.v1 contract. Use when the user says "open a CAPA for NCR <id>", "work the nonconformance", "start the 8D", or when a CAPA run begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# NCR Intake
## Purpose
Turn the source NCR, complaint log and inspection data into the CAPA entry payload.
## When to use
Start of every CAPA run - typically on handoff from Quality Inspection & Nonconformance.
## Inputs
The NCR contract payload or NCR document (JSON/text/PDF); complaint/defect log export (CSV/XLSX); inspection data. Emits the entry hop of mfg.quality-incident-capa.v1 (schema in contracts/).
## Steps
1. Extract ncr_ref (NCR id, part, lot, defect, disposition) from the source NCR - preserve its citations.
2. Load the complaint log for the window (default 180 days); keep part_number, machine, cause_category, date per row.
3. Note any closure-pressure language in the record verbatim (it gets surfaced, not obeyed).
4. Validate against the contract; write capa-intake.json + complaints.csv.
## Output
capa-intake.json + complaints.csv - the entry hop.
## Grounding requirements
ncr_ref carries the source NCR's citations; complaint rows keep their log row identity.
## Constraints
- No root-cause opinions here - that is root-cause-analyze's job.
- Never drop complaint rows because they belong to other parts - the systemic test needs them.
## Escalation / uncertainty
Missing complaint log or window ambiguity: ask the quality engineer; record in escalations[].
