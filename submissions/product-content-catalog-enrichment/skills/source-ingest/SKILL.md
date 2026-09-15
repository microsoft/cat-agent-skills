---
name: source-ingest
description: Ingests supplier spreadsheets, spec sheets and copy into the rtl.product-content-enrichment.v1 contract. Use when the user says "enrich these SKUs", "supplier sent the item sheet", "get these products channel-ready", or an enrichment batch begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising}
---
# Source Ingest
## Purpose
Structure the supplier package: one record per SKU with GTIN, raw supplier fields verbatim, and the supplier's marketing copy as supplied.
## When to use
Start of every enrichment batch.
## Inputs
Supplier spreadsheet (CSV/XLSX), spec sheets/manuals (PDF/text), target channel and market. Emits the entry hop (schema in contracts/).
## Steps
1. Extract per SKU: gtin (verbatim digits), supplier_fields {column: value} exactly as supplied, row reference.
2. Keep supplier copy as a field - it is INPUT to the claim check, never pre-approved copy.
3. Record batch_id, supplier, channel; validate; write batch.json.
## Output
batch.json - the entry hop.
## Grounding requirements
Every SKU cites its sheet row; nothing is corrected silently (a wrong GTIN must FAIL validation, not be fixed here).
## Constraints
- No normalisation, scoring or copywriting here.
## Escalation / uncertainty
Unreadable rows -> listed and escalated to the steward (#5).
