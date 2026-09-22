---
name: ecr-ingest
description: Reads the engineering change request, spec/drawing delta and BOM export into the mfg.engineering-change-bom.v1 contract. Use when the user says "assess this change request", "work ECR <id>", "what does this change touch", or when an engineering-change run begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Engineering}
---
# ECR Ingest
## Purpose
Normalize the ECR, the proposed delta and the BOM/document exports into the contract entry payload.
## When to use
Start of every engineering-change run.
## Inputs
ECR (text/PDF/form extract); drawing or spec delta; BOM export (CSV/JSON, parent-child links with interface flags); document register export; inventory snapshot. Emits the entry hop of mfg.engineering-change-bom.v1 (schema in contracts/).
## Steps
1. Extract ecr_id, part_number, change_type (from the controlled list), affected_characteristic, description - keep the requester's wording verbatim, including any "minor change" framing (surfaced, not obeyed).
2. Load the BOM links (child, parent, qty_per, interface_critical) and the document register rows.
3. Validate against the contract; write ecr.json, bom.json, docs.json, inventory.json.
## Output
Structured entry payload - the ECR hop.
## Grounding requirements
change_type maps to the controlled vocabulary; BOM links and register rows keep their export identity as citations.
## Constraints
- Never drop the interface_critical flag from a BOM link; the interface rule depends on it.
- No impact claims here - that is bom-impact's job.
## Escalation / uncertainty
Ambiguous change_type or characteristic id: ask the requesting engineer; record in escalations[].
