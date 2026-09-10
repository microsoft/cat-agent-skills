---
name: term-retrieve
description: Retrieves the governing trade terms, promotion calendar entries and agreements for the customer and period. Use on "what did we actually sign", "what's the agreed rate", after claim-ingest.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Revenue Growth Management}
---
# Term Retrieve
## Purpose
The signed truth: terms with rates, periods, signature status - quoted verbatim.
## When to use
After claim-ingest in every case.
## Inputs
config/trade-terms.json + TPM/contract repository.
## Steps
1. Retrieve terms for customer + period; quote rate/amount, term id, signature status.
2. Unsigned drafts are retrieved but marked unsigned - they match nothing (#1.1).
## Output
Terms attached for matching.
## Grounding requirements
Term id + agreement citation on every quote.
## Constraints
- Retrieval only; a rate remembered from the negotiation is not a term.
## Escalation / uncertainty
Version ambiguity -> #4 floor, trade manager confirms the governing version.
