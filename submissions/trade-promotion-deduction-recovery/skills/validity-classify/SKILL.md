---
name: validity-classify
description: Classifies deduction validity and quantifies the disputable amount with the calculation shown - the explicit Govern step - and runs promotion lift only where the RGM scoping allows. Use on "is this deduction valid", "how much can we dispute", "should we write it off", after claim-match.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Revenue Growth Management}
---
# Validity Classify (Govern)
## Purpose
The compliance determination IS the work: valid / partial / unsupported with entitled-vs-claimed arithmetic shown (#2.1-#2.3). Lift runs only with the account P&L foundation (#3.1).
## When to use
After claim-match in every case; on any write-off question.
## Inputs
matched.json + config/rgm-scoping.json (+ scan extract when lift is in scope).
## Steps
1. Run scripts/deduction_classify.py --matched matched.json --scoping rgm-scoping.json --out governed.json
2. Quote verdicts and calculations verbatim. "Not worth chasing" is a business decision a human takes with the number in front of them - the engine quantifies, it never writes off (#2.4).
3. If scoping skips lift, say so and why - scoped-out is a design decision, not a failure (#3.1).
## Output
governed.json - the {validity, promo_lift} hop.
## Grounding requirements
Every verdict cites the signed term and rule section; every disputable amount shows its calculation.
## Constraints
- The engine decides; the model never adjusts an entitled amount or softens a partial to valid.
- No credits posted, no write-offs, no term changes (plugin boundary).
## Escalation / uncertainty
Confidence < 0.75 -> analyst review before the dispute goes out (#4).
