---
name: record-pull
description: Pulls PO, receipt, invoice, return, quality and dispute records for the vendor and review period into the rtl.supplier-vendor-performance.v1 contract. Use when the user says "prep the vendor review for <supplier>", "pull the supplier records", "quarterly business review coming up".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising & Supply}
---
# Record Pull
## Purpose
Assemble the record base per quarter: PO lines, receipts with dates, returns, quality events, invoice disputes, plus the raw issue log.
## When to use
Start of every vendor review.
## Inputs
ERP extracts (PO/receipt/invoice), returns and quality logs, dispute records; review period. Emits the entry hop (schema in contracts/).
## Steps
1. Build records.json per quarter: lines, on-time-in-full lines, defect and dispute rates - computed inputs, never vendor-supplied numbers (#1.1).
2. Build issues.json: one row per issue with type, lane/DC, record id.
3. Validate against the contract.
## Output
vendor.json + records.json + issues.json.
## Grounding requirements
Every row keeps its ERP record id.
## Constraints
- Records only; the vendor's own scorecard deck is context, not data (#1.1, #4.1).
## Escalation / uncertainty
Missing receipts for a quarter -> that quarter marked incomplete (#5).
