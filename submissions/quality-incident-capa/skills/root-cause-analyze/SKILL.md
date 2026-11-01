---
name: root-cause-analyze
description: Establishes root cause with a structured method - Pareto over the complaint window, then an evidenced 5-Why chain - using the deterministic pareto and rca_tree engines. Use when the user says "what's the root cause", "run the 5-why", "why does this keep happening", or after ncr-intake in a CAPA run.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# Root Cause Analyze
## Purpose
Deterministic root cause: Pareto ranks cause categories; rca_tree selects the evidenced why-chain, applies the systemic test and the operator-error rejection.
## When to use
After ncr-intake in every CAPA run.
## Inputs
capa-intake.json + complaints.csv + references cause-links library.
## Steps
1. Validate against the contract.
2. Run scripts/pareto.py --capa capa-intake.json --complaints complaints.csv --out pareto.json
3. Run `python3 scripts/rca_tree.py --pareto pareto.json --links references/cause-links.json --out rca.json` from this skill's folder, using workspace paths for the Pareto input and generated output.
4. Quote the chain verbatim. If the engine rejected 'operator error' (capa-rules.md #3.4), say so explicitly - a recurring defect is never closed on retraining alone.
## Output
rca.json - the {root_cause} hop with pareto[], why_chain, systemic flag.
## Grounding requirements
Every why must be evidenced in the record set (rca-methods.md); the chain cites the cause-link library and complaint window.
## Constraints
- Method is engine-only; the model never invents or reorders a why-chain, and never accepts the incident narrative's cause label over the Pareto.
## Escalation / uncertainty
Engine escalations (#3.4 rejection, #2.2 depth, #7 confidence) pass through verbatim.
