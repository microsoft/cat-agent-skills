---
name: tolerance-check
description: Compares actual measurements against spec tolerances for an inspection lot, computes per-characteristic statistics, flags out-of-tolerance and marginal characteristics, and cross-checks certificate claims against measured reality - deterministically. Use when the user says "check tolerances", "compare against spec", "any out-of-spec?", or after spec-ingest completes in a lot review.
license: MIT
metadata:
  version: "2.0"
  author: Microsoft Manufacturing Skills
  category: Quality
---
# Tolerance Check
## Purpose
Deterministically compute deviation status, statistics and certificate cross-checks for every characteristic in the lot.
## When to use
After spec-ingest, in every lot review.
## Inputs
characteristics.json + measurements.csv + coc.json from spec-ingest (contract mfg.quality-inspection.v1 inputs).
## Steps
1. Validate inputs against the contract.
2. Run scripts/tolerance_check.py --spec characteristics.json --measurements measurements.csv --coc coc.json --out deviations.json
3. Quote the engine output verbatim - statuses, statistics, band consumption, incidence. Never restate or recompute a number in prose.
4. If any characteristic carries doc_conflict=true, lead with it: the certificate says one thing, the measurements say another, and measurements govern (disposition-rules.md #4.3).
## Output
deviations.json - the {deviations} hop: characteristics[] with stats, status, doc_conflict, confidence, source=engine:tolerance_check, citations.
## Grounding requirements
Every characteristic row carries the drawing citation forwarded from spec-ingest; conflicts cite the certificate ID and the rule.
## Constraints
- All math happens in the engine.
- No severity or disposition talk here - that is defect-grade's job.
- A certificate claim never suppresses a measured nonconformance.
## Escalation / uncertainty
Engine escalations (missing tolerance #4.4, doc conflict #4.3) pass through verbatim to the payload and the eventual NCR.
