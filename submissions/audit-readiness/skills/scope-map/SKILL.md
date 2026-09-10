---
name: scope-map
description: Maps the audit scope to the standard's clauses and required evidence types with the deterministic clause_map engine. Use when the user says "we have an audit coming", "map the audit scope", "what clauses apply", or when an audit-readiness run begins.
license: MIT
metadata: {version: "1.0", author: Microsoft Manufacturing Skills, category: Quality}
---
# Scope Map
## Purpose
Deterministic scope-to-clause mapping: which clauses apply, what evidence each requires, how fresh it must be.
## When to use
Start of every audit-readiness run.
## Inputs
Audit notice (standard, date, scope areas, active roles); clause table reference. Emits the entry hop of mfg.audit-readiness.v1 (schema in contracts/).
## Steps
1. Extract audit_id, standard, audit_date, scope[], active_roles, clause owners from the notice.
2. Run `python3 scripts/clause_map.py --audit audit.json --clauses references/clause-table.json --out mapped.json` from this skill's folder, using workspace paths for the audit input and generated output.
3. Quote the clause list verbatim.
## Output
mapped.json - the {clause_map} hop.
## Grounding requirements
Every clause row cites the clause table; scope comes from the audit notice verbatim.
## Constraints
- No readiness opinions here; mapping only.
## Escalation / uncertainty
Unknown standard or ambiguous scope: ask the audit lead; record in escalations[].
