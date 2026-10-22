# Report spec (input for `scripts/render_report.py`)

Write a UTF-8 JSON file with these keys. `title` is required, plus `recommendation` (connectivity)
and/or `positioning` (Joule vs Copilot Studio, where to extend). Omit empty sections. Keep strings
plain text (no HTML); the renderer escapes everything.

```json
{
  "title": "Contoso – PO approvals in Teams from S/4HANA",
  "subtitle": "SAP ↔ Power Platform integration architecture",
  "date": "2026-10-21",
  "verification": {"mode": "live", "date": "2026-10-21",
                   "notes": ["OAuth 2.0 on SAP OData connector still preview"]},
  "summary": "One or two sentences with the decision.",
  "facts": [{"topic": "SAP product", "value": "S/4HANA 2023, RISE on Azure", "source": "document: landscape.docx"}],
  "positioning": [{
    "question": "Joule or Copilot Studio?",
    "options": [
      {"id": "J1", "name": "Joule ↔ Microsoft Copilot integration", "fit": "recommended", "why": "Standard PO status questions are already covered by Joule"},
      {"id": "J2", "name": "Copilot Studio agent → SAP", "fit": "complementary", "why": "Approval flow spans SAP and Teams"},
      {"id": "J5", "name": "Joule Studio custom agent", "fit": "not a fit", "why": "Approvers don't work in SAP apps"}
    ],
    "together": ["One identity foundation: Entra ID ↔ SAP Cloud Identity Services trust"]
  }],
  "recommendation": {
    "id": "P3", "name": "SAP OData connector + Azure API Management",
    "confidence": "high",
    "why": ["SAP runs on RISE in Azure → VNet peering, no extra proxy"],
    "identity": "Entra ID user → APIM converts OAuth to SAML → SAP named user (principal propagation)"
  },
  "flow": ["Copilot Studio agent", "SAP OData connector", "Azure API Management", "VNet peering", "S/4HANA (RISE)"],
  "identity_flow": ["Entra ID token", "APIM policy", "SAML assertion", "SAP user"],
  "alternatives": [{"id": "P4", "name": "SAP BTP + Cloud Connector", "when": "If BTP becomes the API front door"}],
  "prerequisites": [{"role": "SAP Basis", "item": "Activate the purchase order OData service (verify name in SAP Business Accelerator Hub)"}],
  "steps": [{"phase": "Pilot", "items": ["Expose one read service through APIM"]}],
  "risks": [{"risk": "Licensing of a shared technical user", "severity": "high", "mitigation": "Confirm with SAP account team"}],
  "open_questions": ["Is SAP Cloud Identity Services already federated with Entra ID?"],
  "sources": [{"title": "Copilot Studio with SAP", "url": "https://learn.microsoft.com/..."}]
}
```

Field rules:
- `verification.mode`: `live` (checked with a lookup tool) or `baseline`.
- `confidence` and `severity`: `high`, `medium` or `low`.
- `positioning[].options[].fit`: `recommended`, `complementary` or `not a fit`.
- `id` fields are optional internal references (P1–P9, J1–J6, E1–E5) and are **not displayed**;
  make every `name` a plain, self-explanatory label.
- `flow` / `identity_flow`: 2–7 short labels each; they become the diagrams.
- `source` on facts: `user`, `document: <file>` or `assumption`.
