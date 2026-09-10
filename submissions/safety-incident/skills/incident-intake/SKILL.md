---
name: incident-intake
description: Receives a safety-incident report from a form, email or voice note and pulls it into the mfg.safety-incident-assist.v1 contract inputs. Use when the user says "log this incident", "new incident report", "someone got hurt", "intake this near miss", "process this safety report", or when a Safety Incident Agent run begins.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: EHS
---

# Incident Intake

## Purpose
Turn an incident report arriving from any channel — a web/paper form, an email, or a voice-note
transcript — into structured contract inputs: the incident identity, area/asset, what happened,
the injury detail (body part, nature, treatment given, outcome, days away), witnesses, and the
immediate actions taken. This is the entry payload every later skill builds on.

## When to use
- "Log this incident" / "intake this near miss" / "process this safety report".
- A report arrives by form, email or voice note (transcript).
- Start of any Safety Incident Agent run.

## Inputs
- Incident report in any channel: form (TXT/JSON), email (TXT), or voice-note transcript (TXT/VTT).
- Witness statements, first-aid / first-responder notes.
- Asset/area register (XLSX/CSV): area, asset tag, shift, supervisor.
- Emits inputs for contract `mfg.safety-incident-assist.v1`.

## Steps
1. Identify the report channel and set `report_channel` (form | email | voice).
2. Extract the factual account into `description`; capture `occurred_at`, `reported_at`,
   `reported_by`, `asset_or_area`, `location`.
3. Structure the injury into `injury{}`: `body_part`, `nature`, `treatment_given`
   (none | first_aid | medical_treatment | hospitalization), `outcome`
   (none | days_away | restricted_duty | job_transfer | in_patient_hospitalization | amputation |
   loss_of_eye | fatality), and `days_away`. Map free text to these controlled values — never invent
   a treatment or outcome not stated in the report.
4. Capture `witnesses[]` and `immediate_actions`; set `incident_type`
   (injury | illness | near_miss | property | environmental).
5. Produce `incident-intake.json` with `contract_version`, `incident_id`, `asset_or_area`, the
   fields above, and an empty `history{}`.

## Output
`incident-intake.json` conforming to the contract inputs — the entry payload of the flow.

## Grounding requirements
Every extracted fact cites its source line (form field, email line, or transcript). The controlled
treatment/outcome values map to `references/osha-recordability-rules.md` #2-#3; the area/supervisor
cite the register row.

## Constraints
- Do not classify severity or recordability here — that is the recordability engine's job
  (engine/LLM split).
- Map free text to the controlled treatment/outcome vocabulary; do not guess a value the report
  does not support. An ambiguous treatment/outcome is an escalation, not a guess.
- Never downgrade or soften a reported injury ("just a scratch") — record what the report states.

## Escalation / uncertainty
- Treatment or outcome unclear, the injured person's status unknown, or the area untraceable: record
  it in the contract `escalations[]` and flag for confirmation; do not fabricate a value.
