# RCA & Standards — Excerpts (grounding)

Reference excerpts the `incident-writeup` skill cites when drafting the incident summary and the
root-cause-analysis template. Grounded in **ISO 45001** (OH&S management systems), **OSHA
300/300A** recordkeeping, and **JHA/HIRA** practice. Cited as `rca-standards-excerpts.md #<section>`.

## 1. ISO 45001 — incident investigation (clause 10.2)

Organizations must investigate incidents to determine root causes, evaluate the need for corrective
action, and act to prevent recurrence — including a review of whether hazards/risks were adequately
assessed (i.e., loop back to the JHA/HIRA). The write-up should therefore always link the incident
to (a) the failed or missing control and (b) the corrective action that closes the gap.

## 2. OSHA 300 / 300A recordkeeping

- **OSHA 300 log** — each recordable case is a line entry with the classification column:
  `G` death · `H` days away · `I` job transfer/restriction · `J` other recordable.
- **OSHA 300A summary** — the annual summary of the 300 log, posted Feb 1-Apr 30.
- The drafted summary must state the recordability determination and the column so the EHS manager
  can transcribe the entry directly.

## 3. Incident summary — required elements

A complete drafted summary carries: incident ID, date/time, area/asset, people involved, a factual
description (what happened, in sequence), the classification (severity, recordable + column,
reportable + clock), immediate actions taken, and the assigned investigator + notified owners.
State facts, not blame.

## 4. Root-cause template (5-Why / fishbone)

**5-Why** (minimum, all cases): state the problem, then ask "why" iteratively (typically 5 times)
until a systemic cause is reached; attach a corrective action to the root, not the symptom.

**Fishbone / Ishikawa** (high & critical cases): organize contributing factors under the standard
categories — **People, Process/Method, Equipment/Machine, Materials, Environment, Management** — to
avoid stopping at "human error." Each identified factor gets a corrective action with an owner and
a due date.

Template skeleton the write-up emits:
- Problem statement (the deviation, measurable)
- 5-Why chain (Why 1 -> ... -> root cause)
- Contributing factors (fishbone categories, for high/critical)
- Failed/missing control (tie back to the JHA/HIRA — ISO 45001 #1)
- Corrective actions (owner, due date, verification)

## 5. JHA / HIRA linkage

Every RCA checks the Job Hazard Analysis / Hazard Identification & Risk Assessment for the task: was
the hazard identified? was the control adequate and in place? If the hazard was missing or the
control failed, the JHA/HIRA is updated as a corrective action before the task returns to service.
