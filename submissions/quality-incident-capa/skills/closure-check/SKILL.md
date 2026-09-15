---
name: closure-check
description: Validates CAPA closure readiness against the closure rules - the explicit Govern step of this plugin. Use when the user says "can we close this CAPA", "is the 8D ready to close", "close it out", or before any closure recommendation.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# Closure Check (Govern)
## Purpose
Deterministic closure gate per capa-rules.md #6: containment, verified root cause, CA (+PA if systemic), complete effectiveness checks, verification evidence. Compliance determination IS the work here.
## When to use
On any closure question, and before eightd-draft finalizes.
## Inputs
capa.json (closure{} populated by capa_logic).
## Steps
1. Validate against the contract.
2. Read closure.ready and closure.blockers[] from the engine output; quote them verbatim.
3. A CAPA with blockers is presented as OPEN with named blockers - never as "basically done".
## Output
Confirmed closure{} - the Govern hop.
## Grounding requirements
Every blocker cites its rule section.
## Constraints
- The model never closes a CAPA; it reports the engine's gate and the human decides.
- Schedule pressure ("close by Friday") never removes a blocker.
## Escalation / uncertainty
ready=false with pressure to close: escalate to the quality manager explicitly.
