---
name: fault-intake
description: Reads maintenance fault notes, operator reports, alarm/event logs, asset IDs and location into the mfg.maintenance-triage.v1 contract inputs. Use when the user says "triage this fault", "work this breakdown", "read the fault note for <asset>", "what's wrong with pump <id>", or when a maintenance triage run begins.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Fault Intake

## Purpose
Turn the raw breakdown inputs (technician fault note, operator report, alarm/event log,
asset tag) into structured contract inputs: a normalized symptom list, alarm codes, the
asset identity, and its criticality/downtime attributes.

## When to use
- "Triage fault on <asset>" / "work this breakdown" / "what's wrong with <asset>?"
- "Read the fault note / alarm log for <asset>."
- Start of any Maintenance Triage run.

## Inputs
- Fault note / operator report (TXT, email, or extract): free-text symptoms.
- Alarm / event log (CSV): timestamped alarm codes for the asset.
- Asset register + criticality (XLSX / CSV): class (A/B/C), downtime cost/hr, redundancy.
- Emits inputs for contract `mfg.maintenance-triage.v1`.

## Steps
1. Confirm the asset tag resolves in the asset register; carry its criticality class,
   `downtime_cost_per_hr`, and `redundancy` onto the contract.
2. Map free-text symptoms to the controlled vocabulary in
   `references/failure-mode-library.md` #1 (e.g. "runs hot and trips" -> `overload_trip`,
   `motor_hot`). Never invent a symptom that is not evidenced.
3. Extract alarm codes from the event log as `alarm_codes[]`.
4. Produce `fault-intake.json` with `contract_version`, `asset_id`, `asset_criticality`,
   `downtime_cost_per_hr`, `symptoms[]`, `alarm_codes[]`, and an empty `history{}`.

## Output
`fault-intake.json` conforming to the contract inputs — the entry payload of the flow.

## Grounding requirements
Every symptom cites the source line (fault note or alarm log). Asset attributes cite the
asset register row.

## Constraints
- Symptom vocabulary is fixed by `references/failure-mode-library.md` #1 — map, do not guess.
- Do not rank causes or set priority here — that is the Analyze skills' job (engine/LLM split).
- Never fabricate an asset attribute; a missing tag or criticality is an escalation.

## Escalation / uncertainty
- Asset tag not found, criticality class missing, or symptoms un-mappable: stop and ask the
  technician; record it in the contract `escalations[]`.
