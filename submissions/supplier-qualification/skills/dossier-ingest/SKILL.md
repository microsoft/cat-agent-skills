---
name: dossier-ingest
description: Gathers the supplier's qualification documents - certificates, financials, audit reports, PPAP elements - into the mfg.supplier-qualification.v1 contract. Use when the user says "qualify this supplier", "review the supplier package", "new vendor for <category>", or when a qualification run begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Supply Chain}
---
# Dossier Ingest
## Purpose
Normalize the supplier package into the structured dossier the engines score.
## When to use
Start of every qualification run.
## Inputs
Certificates (PDF/text), financial summary (CSV/XLSX/text), audit report, PPAP element list, category + as-of date. Emits the entry hop of mfg.supplier-qualification.v1 (schema in contracts/).
## Steps
1. Extract cert: standard, doc id, EXPIRY DATE (verbatim - validity is decided by the engine, never by the cert's presence).
2. Extract financials: quick ratio, trend across periods. Extract audit score. List PPAP elements present.
3. Record region, category, category regional concentration, and the required PPAP set for the category.
4. Validate against the contract; write dossier.json.
## Output
dossier.json - the entry hop.
## Grounding requirements
Every dossier field cites its source document; sales claims in cover letters are recorded as claims, not facts.
## Constraints
- Never mark a cert "valid" - extract the expiry and let risk_score decide (#1.1).
- No scoring or recommendation here.
## Escalation / uncertainty
Missing financials or unverifiable documents: record and continue - the engine applies the confidence floor (#6).
