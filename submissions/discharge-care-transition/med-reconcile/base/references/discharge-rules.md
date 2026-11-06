# Discharge & Care-Transition Rules
Companion to the deterministic engines. Every engine constant mirrors a numbered rule below, line for line.
Engines: `med_reconcile` (#1, #4-#9), `readability_check` (#3), `followup_check` (#10-#11).
Starter grounding - a facility replaces this file with its own SOP and edits `config/` only.

## #1 Medication reconciliation is a diff, never a silent carry-forward
`med-reconcile` computes expected_discharge_meds by applying admission_meds + inpatient_changes (stops removed,
starts added, changes applied), then diffs it against draft_discharge_meds. Any admission medication that was
stopped in-house for a documented reason and reappears in draft_discharge_meds without a new order is an
**unresolved discrepancy** - it is never silently dropped from the diff or silently allowed through. A later
documented `start` of the same drug is that new order: it supersedes the earlier stop, so the drug is expected
(active) and is no longer listed on `reconciliation_report.stopped_meds` (1.0.3).
Engine discrepancy type: `unresolved_stop_reappeared`.

## #2 Discharge summary is a legal record
`summary-draft` output requires clinician signature before it enters the record. The plugin marks everything draft.
Action level L1 (draft prepared, human approves). No engine type - enforced by skill constraint.

## #3 Patient instructions are plain language, not a simplified copy of the clinical summary
`patient-instructions` is derived from the same evidence as the clinical summary and is **independently checked
for reading level by the `readability_check` engine**, not self-asserted. The metric, the grade-level threshold,
the maximum sentence length, the banned-jargon list and the required sections all come from
`config/readability-rules.json`; no threshold is hard-coded. A draft that exceeds the configured grade level, uses
a banned jargon term, runs a sentence past the configured word limit, or omits a required section **fails** the
check and escalates. A required section whose only content is the clinician marker
`[CLINICIAN TO COMPLETE: ...]` has not been written and counts as missing (1.0.2). A banned jargon term written in
lower case also matches its inflected forms (-s, -es, -ed, -ing, final silent e dropped: `titrate` catches
`titrated`); an abbreviation (any capital or digit, e.g. `NPO`, `q4h`) matches exactly (1.0.3).
Activity, Diet and When-to-call lines are sourced only from a cited
`discharge_instruction_notes[]` entry on the contract (1.0.2). Engine report: `readability_report`.

## #4 A medication expected on discharge must appear on the discharge draft
Any medication on expected_discharge_meds that is absent from draft_discharge_meds is a discrepancy - an active
medication silently lost at the transition is a patient-safety event, not an omission of convenience. An expected
active medication that the draft lists with a stop status (`stopped`, `discontinued`, `held`) when no inpatient stop
order exists counts as absent.
Engine discrepancy type: `missing_from_discharge`.

## #5 A medication stopped in-house must be explicitly documented as stopped - deleting it is not resolving it
A drug stopped during the stay must appear in draft_discharge_meds carrying a stop status (`stopped`,
`discontinued` or `held`) with the stop reason, so the patient, the pharmacy and the receiving clinician can all
see the decision. **Removing the drug from the draft entirely is itself a discrepancy** and never produces a clean
reconciliation: hiding the problem is not allowed to be the cheapest path. A stopped drug listed with a stop status
but no stop reason (`reason` empty or absent on the draft entry) is not documented either and is the same
discrepancy (1.0.3). The engine also lists every in-house stop, with its reason and citation, on
`reconciliation_report.stopped_meds` so the discharge summary shows what was discontinued even when reconciliation is
clean, and the patient instruction sheet tells the patient in plain words to stop or hold each one that has no open
discrepancy.
Engine discrepancy type: `stopped_med_undocumented`.

## #6 Nothing appears on the discharge list that was not on admission or started in-house
A drug in draft_discharge_meds that is on neither admission_meds nor an inpatient `start` change has no order
behind it. It is reported as an unordered addition and blocks a clean reconciliation.
Engine discrepancy type: `unordered_addition`.

## #7 A dose mismatch is never cosmetic
Where the draft dose differs from the expected dose, the difference is always listed.
Engine discrepancy type: `dose_mismatch`.

## #8 A documented change must apply to a medication that is actually on the expected list
A `change` action naming a drug that is not on the expected list (never on admission, or already stopped) is never
silently ignored - it is reported so the clinician can say which record is wrong.
Engine discrepancy type: `change_to_absent_med`.

## #9 Every medication action carries its documenting note and date
Each entry in inpatient_changes must cite `source_note` and `documented_date`; each admission medication cites its
`source_note`. The citation rides the contract onto expected_discharge_meds and onto every discrepancy, so
provenance survives every hand-off. An inpatient change without a documenting note and date is a discrepancy.
Engine discrepancy type: `change_provenance_missing`.

## #10 Every follow-up item and pending result is owned and dated
`followup-plan` items and pending results must each carry the fields listed in `config/followup-rules.json`
(`item`/`result`, `owner`, `due_date`, `source_note`), and the owner must be one of the configured allowed owners.
A missing field, or an owner outside the configured set, is a gap and escalates rather than being left blank.
Every pending result and referral order must also appear on the follow-up checklist (matched on its `source_note`);
one that does not is a gap.
Engine report: `followup_report`; gap types `missing_field`, `owner_not_allowed`, `untracked_order`.

## #11 Follow-up dates fall inside the configured window
A follow-up due date later than `max_days_to_first_followup` days after the discharge date, or earlier than the
discharge date, is a gap - dates come from orders, never from invention. A due date that is not an ISO date
(YYYY-MM-DD), or a missing or unreadable encounter discharge date, means the window cannot be verified - that is a
gap too, so the checklist is never complete without a checkable date.
Engine gap types: `due_date_out_of_window`, `due_date_unverifiable`.
