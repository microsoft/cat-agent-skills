---
name: store-map
description: Retrieves the store profile - format, cluster, fixtures, received assets, completed tasks, prior execution history - for the readiness test. Use after pack-ingest, or when the user asks "what does this store actually have".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Store Operations}
---
# Store Map
## Purpose
Assemble the store side of the readiness equation: profile + what is physically confirmed on site.
## When to use
After pack-ingest in every run.
## Inputs
Store master export (format, cluster, fixtures); receiving confirmations; task-system export; current shelf-price extract.
## Steps
1. Build store.json: store_id, format, cluster, fixtures[], received_assets[], completed_tasks[].
2. Build shelf-prices.json from the POS/price extract - current shelf price per SKU.
3. Keep export identities as citations.
## Output
store.json + shelf-prices.json.
## Grounding requirements
Fixtures and confirmations come from records, never assumptions ("it always has an end-cap" is not a record).
## Constraints
- Mapping only; the readiness verdict belongs to the engine.
## Escalation / uncertainty
Missing store profile blocks readiness (#6) - ask store ops for the profile.
