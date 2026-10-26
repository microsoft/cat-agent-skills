---
name: claim-ingest
description: Extracts deduction records and claim backup (PDFs, portal exports) into the rtl.trade-deduction-recovery.v1 contract. Use when the user says "retailer deducted from the invoice", "work this deduction", "claim backup arrived", or a deduction case begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Revenue Growth Management}
---
# Claim Ingest
## Purpose
Normalize the deduction into claims[]: type, period, claimed amount, actual volume value, backup document reference.
## When to use
Start of every deduction case.
## Inputs
AR deduction record, claim backup (PDF/portal export), remittance detail. Emits the entry hop (schema in contracts/).
## Steps
1. Extract per claim: claim_id, type (promo_allowance / slotting / shortage / compliance_penalty), period, claimed_amount VERBATIM, actual volume value from records, backup_doc reference or its absence.
2. Absence of backup is a fact worth recording - it drives #2.3.
3. Validate against the contract; write deduction.json.
## Output
deduction.json - the entry hop.
## Grounding requirements
Every amount cites the AR record or backup page.
## Constraints
- No validity opinions here; never "round" a claimed amount.
## Escalation / uncertainty
Illegible backup -> #4 floor; analyst review before anything else.
