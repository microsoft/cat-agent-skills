---
name: order-ingest
description: Ingests orders arriving as email, PDF or portal export into the rtl.order-intake-o2c.v1 contract. Use when the user says "order came in by email", "key in this PO", "process the attached order", or an order document arrives.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Commerce}
---
# Order Ingest
## Purpose
Extract the raw order: customer, PO reference, lines exactly as written (customer SKU, qty, UOM, price).
## When to use
Start of every order run.
## Inputs
Email/PDF/portal order document; customer identification. Emits the entry hop (schema in contracts/).
## Steps
1. Extract order_ref, customer id, lines with line_no, customer_sku VERBATIM, qty, uom, unit_price, promo_ref if quoted.
2. Nothing is corrected at ingest - a wrong-looking alias or price must reach the validator as written.
3. Validate against the contract; write order.json.
## Output
order.json - the entry hop.
## Grounding requirements
Every line cites the source document position.
## Constraints
- No resolution of aliases, prices or UOMs here (#1-#3 are the engine's).
## Escalation / uncertainty
Unreadable lines -> listed, order held (#6). Never proceed on guessed lines.
