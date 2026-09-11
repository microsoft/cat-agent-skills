---
name: inquiry-intake
description: Takes the customer inquiry from any channel and classifies intent against the taxonomy with the deterministic intent_classify engine. Use when a service inquiry arrives - "where is my order", "it says delivered but I never got it", "can I return this", "is it in stock", "how do I set this up".
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Customer Operations}
---
# Inquiry Intake
## Purpose
Structured inquiry + deterministic intent (#1.1). DNR outranks generic WISMO when both match - the contradiction path is safety-relevant.
## When to use
Start of every service run.
## Inputs
Inquiry text verbatim (chat/email/voice transcript), channel, customer id, order reference; the records extract that ships with the case (records.json - OMS order, carrier scans, loyalty); config/service-config.json. Emits the entry hop (schema in contracts/).
## Steps
1. Capture text verbatim; record channel/tone; note explicit asks (refund now, goodwill credit) as flags.
2. Run scripts/intent_classify.py --inquiry inquiry.json --config service-config.json --out classified.json
3. Below the confidence floor -> the run is a handoff, never a guessed answer (#1.1).
4. Intake is a hop, not a stopping point. Continue to context-assemble in the same run; do not pause to ask for records that ship with the case (records.json).
## Output
classified.json - the {intent} hop. Hand straight to context-assemble.
## Grounding requirements
Intent cites the taxonomy; the customer's words stay verbatim.
## Constraints
- No resolution content here; no promises of any kind at intake.
## Escalation / uncertainty
Unclassified or ambiguous -> handoff packet path.
