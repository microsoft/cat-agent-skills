---
name: capa-build
description: Builds corrective and preventive actions with mandatory effectiveness checks from the verified root cause, using the deterministic capa_logic engine. Use when the user says "build the CAPA", "what actions do we take", "corrective actions please", or after root-cause-analyze in a CAPA run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# CAPA Build
## Purpose
Deterministic CA/PA construction: containment (#1), corrective actions traced to the root cause (#2), preventive actions across the systemic scope (#5), an effectiveness check on every action (#4).
## When to use
After root-cause-analyze in every CAPA run.
## Inputs
rca.json + references action library.
## Steps
1. Validate against the contract.
2. Run `python3 scripts/capa_logic.py --rca rca.json --actions references/action-library.json --out capa.json` from this skill's folder, using workspace paths for the RCA input and generated output.
3. Quote actions and checks verbatim; the model may narrate rationale but never adds, drops, or waives an action or check.
## Output
capa.json - the {capa} hop plus closure{} readiness.
## Grounding requirements
Every action cites the action library and its rule section; every check cites #4.
## Constraints
- No action without an effectiveness check; no systemic cause without a PA. The engine enforces it; the model never argues around it.
## Escalation / uncertainty
Blockers from the engine are surfaced, never edited away.
