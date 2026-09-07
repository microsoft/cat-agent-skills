# Process specification schema

```json
{
  "process_name": "Vendor Onboarding",
  "version": "1.0",
  "state": "current",
  "purpose": "Create approved and usable vendor records.",
  "scope": {"starts": "Business submits request", "ends": "Vendor is activated", "exclusions": ["Contract negotiation"]},
  "trigger": "A complete vendor request is submitted",
  "inputs": ["Vendor request", "Tax documentation"],
  "outputs": ["Approved vendor record"],
  "roles": [
    {"name": "Requester", "description": "Provides business need and vendor information"},
    {"name": "Procurement", "description": "Reviews commercial requirements"}
  ],
  "systems": ["Intake portal", "ERP"],
  "steps": [
    {"id": "S1", "name": "Submit vendor request", "type": "task", "owner": "Requester", "description": "Complete the intake form.", "next": "S2", "inputs": ["Vendor details"], "outputs": ["Submitted request"], "system": "Intake portal", "sla": "2 business days", "control_ids": []},
    {"id": "S2", "name": "Is request complete?", "type": "decision", "owner": "Procurement", "description": "Check required fields and documents.", "yes_next": "S3", "no_next": "S1", "control_ids": ["C1"]},
    {"id": "S3", "name": "Create vendor record", "type": "task", "owner": "Finance", "description": "Create the approved vendor in ERP.", "next": null, "control_ids": ["C2"]}
  ],
  "controls": [
    {"id": "C1", "name": "Completeness review", "objective": "Prevent incomplete requests", "owner": "Procurement", "frequency": "Per request", "evidence": "Completed checklist", "type": "preventive"}
  ],
  "risks": [{"id": "R1", "description": "Duplicate vendor creation", "impact": "Incorrect payment or reporting", "mitigation": "Search ERP before creation"}],
  "metrics": [{"name": "Cycle time", "definition": "Submission to activation", "target": "5 business days", "owner": "Procurement Operations"}],
  "improvements": [{"title": "Automate duplicate search", "problem": "Manual search is inconsistent", "recommendation": "Add deterministic duplicate checks", "value": "High", "effort": "Medium", "risk": "Medium", "priority": "P1", "owner": "ERP Product Team"}],
  "assumptions": [],
  "open_questions": []
}
```

## Step types
- `task`
- `decision`
- `start`
- `end`

A task uses `next`. A decision uses `yes_next` and `no_next`.
