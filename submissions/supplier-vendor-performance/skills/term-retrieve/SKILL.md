---
name: term-retrieve
description: Retrieves and quotes the governing contract or trading term for any performance question. Use on "what does the agreement say about OTIF", "do we have a rebate right", or after issue-cluster.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising & Supply}
---
# Term Retrieve
## Purpose
The governing clause, quoted verbatim with its id - the difference between a complaint and a contractual conversation.
## When to use
Any term question; supplements issue-cluster's automatic mapping.
## Inputs
config/trading-terms.json + contract repository.
## Steps
1. Retrieve the clause by topic/vendor; quote text + id + agreement reference.
2. Never paraphrase a remedy - quote it.
## Output
Term citations attached to the payload.
## Grounding requirements
Clause id + agreement version on every quote.
## Constraints
- Retrieval only; interpretation beyond the quoted text goes to legal.
## Escalation / uncertainty
Term ambiguity or version conflict -> legal review item in the pack.
