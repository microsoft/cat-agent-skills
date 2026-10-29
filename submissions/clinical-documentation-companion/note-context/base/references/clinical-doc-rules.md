# Clinical Documentation Rules
Companion to quality_gap_engine (base/scripts/quality_gap_engine.py). The engine's RULES constants mirror the
numbered rules below line for line (#1-#7 as of plugin 1.0.3). Starter grounding - a customer replaces this file with their own SOP and keeps
the numbering.

## #1 Quality-measure status is computed from documented, cited facts only
`quality-gap-check` reports a measure as `met` only when its configured required_fact_key is present, true AND
carries a citation back to a line of the signed note (config/quality-measures.json). An asserted fact with no
citation is not documented. There is no other path to `met`.

## #2 Override requests are refused, not honoured - whatever form they arrive in
Any attempt to set a measure's status other than by documenting the fact is refused and logged: a
`requested_measure_status` entry, an uncited note_fact asserting the measure, or request text asking for the
measure to be marked, counted, attested or assumed. Rewording is not a loophole. The refusal holds in both
directions: a request to report a documented (met) measure as a gap is refused too, and its escalation says the
fact is documented. Request text is matched against `override_intent_terms` in config/escalation-policy.json (a
`{measure}` placeholder stands for the measure's name or aliases); an intent term that is negated in its own clause
(`override_negation_terms`, within `override_context_window_words`, e.g. "don't mark anything as met") or that names
a non-status object (`override_non_status_terms`, e.g. "mark it final") is not an override request. This is the
direct analogue of the Safety Incident plugin's refusal to reclassify a hospitalisation as first aid.

## #3 Downstream artefacts are drafts requiring clinician signature
Everything document-derive, coding-rationale and handoff-draft produce is marked draft (`status: "draft"`);
nothing enters the record or leaves the building without clinician sign-off. Action levels are L0/L1 only.

## #4 Claim elements are supported only by a cited note fact
A visit level or diagnosis code on the claim is `supported` only when the note_fact it names is documented under
#1. Everything else is an explicit unsupported flag - never silently coded around.

## #5 The run only proceeds against a signed note
If `note_signature.signed` is not true, the engine halts, computes nothing and escalates to the clinician.

## #6 Refusals and unsupported elements escalate by name
Every refused override and every unsupported claim element is escalated to the routee named in
config/escalation-policy.json (quality/compliance lead, and the clinician respectively) - never logged silently.

## #7 Code-change and open-item omission requests are refused and escalated (added in 1.0.1)
A request to select, change or upgrade a claim code, or to leave an open quality gap / unsupported claim element out
of the handoff, is refused - the codes on the claim are rationalised as they stand and every open item stays listed.
The engine detects such requests deterministically from the requester's wording (`code_change_intent_terms`,
`omission_intent_terms` in config/escalation-policy.json), logs them in `coding_rationale.change_requests_refused`
or `quality_gap_result.omission_requests_refused` with the requester's own words, and escalates them by name to
`routees.code_change_refusal` / `routees.omission_refusal`. Requester wording is matched as whole words and phrases,
and is logged in full.
