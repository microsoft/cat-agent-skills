---
name: pack-ingest
description: Ingests the HQ campaign pack, price file, planogram and task list into the rtl.store-task-promotion-execution.v1 contract. Use when the user says "new campaign pack landed", "prep the store for the launch", "are we ready for Monday's promo", or when a store assignment arrives.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Pack Ingest
## Purpose
Normalize the campaign pack into requirements[]: assets, tasks, fixtures, applicability (formats/clusters), SKUs, promo prices.
## When to use
Start of every execution run - a pack or assignment arriving.
## Inputs
Campaign pack (PDF/text), price-change file (CSV), planogram/signage list, task list. Emits the entry hop (schema in contracts/).
## Steps
1. Extract campaign_id, launch_date, requirements with req_id, applicability, assets[], tasks[], fixture_required, skus[].
2. Extract promo_prices per SKU from the price file - verbatim numbers; price integrity is the engine's test.
3. Validate against the contract; write pack.json.
## Output
pack.json - the entry hop.
## Grounding requirements
Every requirement cites its pack page/line; prices cite the price file row.
## Constraints
- No readiness opinions here; never drop a requirement because it "obviously" applies everywhere (#1.1 decides).
## Escalation / uncertainty
Ambiguous applicability or missing price file: escalate to HQ retail ops; readiness is blocked without prices (#6).
