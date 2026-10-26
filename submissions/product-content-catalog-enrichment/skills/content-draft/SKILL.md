---
name: content-draft
description: 'Drafts channel descriptions, comparison copy and the review/approval packet from the governed payload. Use to close every enrichment batch: "draft the product copy", "build the review packet".'
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising}
---
# Content Draft
## Purpose
Terminal artifact: channel-ready draft records + approval packet, populated only from the contract payload.
## When to use
End of every enrichment batch.
## Inputs
governed.json (full payload).
## Steps
1. Validate against the contract; blocked claims and invalid GTINs lead the packet.
2. Draft descriptions from normalized attributes and APPROVED claims only (#4.3); flag gaps inline; localisations as requested.
3. Mark DRAFT - the steward approves; nothing publishes to channel.
## Output
Review packet + per-SKU draft records - terminal artifacts.
## Grounding requirements
Every copy statement traces to an attribute or an approved claim.
## Constraints
- Never publish, never approve a regulated claim, never change the taxonomy (plugin boundary).
- A record with an invalid GTIN is drafted as BLOCKED, not published-pending.
## Escalation / uncertainty
Packets with blocked claims route to the claim owner before steward review.
