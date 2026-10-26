---
name: spec-ingest
description: Reads part specs, drawings, inspection plans, certificates of conformance and measurement exports for an inspection lot, and normalizes them into the mfg.quality-inspection.v1 contract inputs. Use when the user says "clear this inspection lot", "load the inspection results", "read the spec for part <PN>", "review lot <LOT-ID>", or when an inspection lot review begins.
license: MIT
metadata:
  version: "2.0"
  author: Microsoft Manufacturing Skills
  category: Quality
---
# Spec Ingest
## Purpose
Turn the lot's raw documents into structured contract inputs: a characteristics table (with tolerances AND criticality, including note-derived criticality), a normalized measurements table, and the certificate's claims.
## When to use
Start of every Quality Inspection & Nonconformance run.
## Inputs
- Part spec / drawing extract (PDF or text): characteristic IDs, nominals, tolerances, notes.
- Inspection plan (text/PDF): which characteristics are checked, sample plan.
- Measurement export (CSV/XLSX from CMM or gauges): per-part values.
- Certificate of conformance (text/PDF), if supplied.
Emits inputs for contract mfg.quality-inspection.v1 (schema in contracts/).
## Steps
1. Verify part number and revision match across drawing, plan, results and CoC. A mismatch blocks the run (disposition-rules.md #4.4).
2. Extract characteristics: name, unit, nominal, lower/upper tolerance, rework note, citation (drawing characteristic ID + revision) - AND criticality. Criticality can come from a table column or from a drawing NOTE (e.g., a note marking a surface fatigue-critical); carry the note as criticality_source. Missing this is how critical defects get graded cosmetic.
3. Extract the CoC's conformity claims into coc{} - each claim lists the characteristics it covers, verbatim claim text, and the certificate citation. Claims are supplier declarations, not verification (ISO 9001 8.4.3).
4. Normalize measurements to rows of {part_serial, characteristic, value}; keep the source file and row as the citation trail.
5. Write characteristics.json, measurements.csv, coc.json.
## Output
characteristics.json + measurements.csv + coc.json - the contract's input hop.
## Grounding requirements
Every characteristic cites its drawing ID + revision (and note number when criticality is note-derived); CoC claims cite the certificate document ID.
## Constraints
- Never guess or interpolate a tolerance; missing tolerance -> not_evaluated, escalate.
- Never proceed on a part-number or revision mismatch.
- Never drop or soften a drawing note - notes carry criticality.
- No deviation math here - that is tolerance-check's job.
## Escalation / uncertainty
Revision mismatch, illegible tolerance, unit ambiguity, or a note whose criticality implication is unclear: stop and ask the quality engineer; record in escalations[].
