---
name: risk-score
description: Scores supplier risk across quality, financial and geographic dimensions with the deterministic risk_score engine. Use when the user says "score this supplier", "how risky are they", "run the risk assessment", or after dossier-ingest in a qualification run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Supply Chain}
---
# Risk Score
## Purpose
Deterministic banded risk: cert validity (#1), PPAP completeness (#4), financial floors (#2), geographic concentration (#3).
## When to use
After dossier-ingest in every run.
## Inputs
dossier.json.
## Steps
1. Validate against the contract.
2. Run scripts/risk_score.py --dossier dossier.json --out scored.json
3. Quote bands and notes verbatim. An expired certificate is HIGH quality risk no matter how impressive the logo - a cert on file is not a cert in force (#1.1).
## Output
scored.json - the {risk} hop.
## Grounding requirements
Every band note cites its rule section; escalations pass through verbatim.
## Constraints
- Banding is engine-only; brand reputation, pricing and sales narrative never move a band.
## Escalation / uncertainty
Missing financials -> confidence floor (#6), sourcing review required.
