---
name: knowledge-retrieve
description: Retrieves the approved knowledge article, policy text or product doc that grounds the answer for the classified intent. Use after context-assemble, or on "what's the approved answer for this".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Knowledge Retrieve
## Purpose
Approved-answer retrieval with citation - the response is grounded or it is a handoff.
## When to use
After context-assemble in every run.
## Inputs
assembled.json + knowledge base / approved scripts / policy documents.
## Steps
1. Retrieve the article(s) matching intent + context; keep article ids and clauses as citations.
2. No article -> the run becomes a handoff with "no approved answer" recorded (#4.1).
## Output
Payload with approved-answer sources attached.
## Grounding requirements
Every answer sentence must be traceable to an article or policy clause.
## Constraints
- Approved sources only; no answers from general knowledge about "how retail usually works".
## Escalation / uncertainty
Conflicting articles -> handoff with both cited.
