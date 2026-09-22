---
name: contradiction-flag
description: Surfaces contradictory evidence - studies moving the same metric in opposite directions - rather than a smoothed answer. Use on "do the studies agree", "any conflicting evidence", after trend-compare.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Insights & Category}
---
# Contradiction Flag
## Purpose
Present BOTH sides with dates and methods (#3.1) - the brief's credibility rests on not smoothing.
## When to use
After trend-compare whenever contradictions[] is non-empty.
## Inputs
compared.json.
## Steps
1. Quote each contradiction verbatim: which studies, which directions, which methods, which periods.
2. Offer the honest framings (method difference, period difference, real reversal) as QUESTIONS for the insight manager, not conclusions.
## Output
Contradiction section for the brief.
## Grounding requirements
Both studies cited fully.
## Constraints
- No midpoint averaging, no "on balance" verdicts; causal attribution is out of scope (#5.1).
## Escalation / uncertainty
Contradiction on the question's core metric -> insight-manager review before the brief ships.
