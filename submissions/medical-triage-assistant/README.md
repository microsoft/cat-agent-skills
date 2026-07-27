# Medical Triage Assistant

A Copilot Studio / Cowork / Scout skill that supports medical teams and health insurance providers with **pre-appointment triage**. It interviews the patient with a structured (non-specialty-specific) questionnaire, receives prior exam documents as photo or PDF, flags out-of-range values descriptively, assigns a 5-level urgency classification (Manchester-inspired), and delivers a **pre-report** that helps the physician prepare the consultation.

## What it does

- Conducts a short, humane triage conversation: chief complaint, onset, intensity, associated symptoms, history, medications in use, allergies.
- Continuously screens for **red flags** — if one appears, it stops the triage, classifies as Emergency and instructs the patient to call the local emergency number immediately (configurable per country/region by the hosting organization), notifying the human team.
- Reads prior exams (photo/PDF), extracts each test with result, unit and the **laboratory's own printed reference range**, and marks values as within/above/below range. A general reference table is used only when the report has no printed range — and it says so.
- Classifies urgency in 5 levels to support scheduling decisions by the human team.
- Produces a complete pre-report from the fixed template, always ending with the mandatory non-diagnostic disclaimer.

## What it NEVER does (by design)

- It never diagnoses ("the patient has X" is forbidden — only descriptive flagging is allowed).
- It never prescribes or suggests medications, dosages, treatments, diets, or medication changes.
- It never gives prognosis or reassurance/alarm about causes.
- It never delivers clinical conclusions to the patient — the pre-report goes to the medical team, and **every output requires evaluation by a licensed physician**.

## Example flow (the endocrinology case)

1. A health-plan member books an appointment with an endocrinologist.
2. The bot runs the triage interview (fatigue, thirst, family history...) and asks whether the patient has recent blood work — the patient sends a photo of a lab report.
3. The skill extracts: fasting glucose 142 mg/dL (lab range 70–99 → **above range**), HbA1c 8.1% (lab range < 5.7% → **markedly outside — physician attention**).
4. It classifies urgency Level 3 (urgent — consider anticipating the appointment), fills the pre-report with the flagged values, observations and suggested questions, and delivers it to the medical team.
5. The physician receives the pre-report before the consultation — diagnosis and treatment remain 100% the physician's.

## Folder structure

```
medical-triage-assistant/
├── metadata.json                     # gallery metadata
├── SKILL.md                          # agent runtime instructions (limits first)
├── README.md                         # this file (human-facing)
├── references/
│   ├── triage_protocol.md            # interview structure, red flags, 5-level classification
│   └── lab_reference_values.md       # fallback adult reference values + flagging language
└── assets/
    └── pre_report_template.md        # fixed pre-report template with mandatory disclaimer
```

## Deployment notes

- **Language**: the skill is written in English and converses with each patient in the patient's own language.
- **Emergency contacts**: the skill is region-neutral by design. Configure your country's emergency number and crisis hotline in the hosting platform (e.g., a variable or system-prompt addition per deployment); without configuration, the skill says "call your local emergency number".
- **Copilot Studio**: connect the agent to the scheduling/CRM flow; deliver the pre-report to the care team's channel (Teams, e-mail, ticket), never to the patient.
- **Privacy**: health data is sensitive personal data under applicable data protection laws (e.g., LGPD in Brazil, GDPR in the EU, HIPAA in the US). The skill collects the minimum needed, masks identifiers outside the care team, and the hosting organization is responsible for storage, consent and retention policies.
- **Compliance**: this skill is a triage *support* tool. It does not replace regulated telehealth services, nurse triage protocols adopted by the institution, or requirements of the local medical regulatory body (e.g., CFM in Brazil). Review with your compliance/legal team before production use.

## References

- Manchester Triage System (5-level urgency model — inspiration for the classification scale)
- American Diabetes Association (ADA) and Sociedade Brasileira de Diabetes (SBD) — glucose/HbA1c thresholds used in the fallback table
- Sociedade Brasileira de Cardiologia (SBC) — blood pressure reference values
- Data protection laws applicable to health data (e.g., LGPD, GDPR, HIPAA)

## Disclaimer

This skill provides administrative and informational triage support. It is not a medical device, does not provide medical advice, and all of its outputs are preliminary and require evaluation by a licensed physician.

---
Author: Michael Ferro Pereira
