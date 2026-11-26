# Prior Authorisation Rules
Companion to criteria_engine (base/scripts/criteria_engine.py). Section numbers are cited verbatim in engine
output, and the engine constants mirror the numbered rules below line for line.

## #1 Criteria checklist is deterministic
`criteria-extract` turns payer policy prose into a fixed checklist per service (config/payer-policy-library.json).
The checklist and its required evidence keys never vary at runtime - only whether the patient record satisfies
each item varies. `request.service` and `request.payer` are required: if either is missing or empty the engine exits 2
with a readable error naming the field and builds no checklist. A library entry applies only when its `payer` equals
`request.payer` (case-insensitive, surrounding spaces ignored); otherwise its checklist is not built, the
determination is `out_of_scope` and the escalation names both payers and routes to the payer-relations contact (#7).
The clause is always the library clause for the service; if `request.clause` or `request.order_clause` (the clause
written on the order, kept verbatim by policy-ingest) is set and differs, the engine keeps the library clause and
escalates the mismatch to the prior-auth coordinator (#7), once per distinct differing value.

## #2 Never an adverse determination - architectural boundary, not a setting
The engine has no "approve" or "deny" output state. Its only possible `determination` values are:
- `packet_assembled_clean` - every required criterion is met and cited;
- `packet_assembled_gaps`  - at least one required criterion is unmet or uncited;
- `out_of_scope`           - the requested service has no policy in config/payer-policy-library.json, or its
  library entry belongs to a different payer than `request.payer` (#1), so no checklist can be assembled. This
  value is produced by the criteria engine (policy-ingest ships no script) and carries an escalation instead of
  improvised criteria.

A request for a determination in EITHER direction - approval or denial - is refused at the engine level
regardless of how the request is phrased. Refusal is symmetric: an "approve it" request and a "just deny it"
request are both refused, and both are logged. Detection is phrasing-independent - it reads `request_mode` and
any free-text intent field on the request against the token lists in #2a, so rewordings
("cleared for scheduling", "mark it medically necessary and approved", "too thin to chase, deny it") are caught
the same way as the literal modes `approve_directly` / `deny_directly`.

Every refusal produces an escalation entry naming the requested direction. Refused silently = defect; honoured
= boundary breach. The determination returned after a refusal is whatever the evidence actually supports
(`packet_assembled_clean`, `packet_assembled_gaps` or `out_of_scope`) - the refusal never changes the result.

### #2a Determination-request tokens (phrasing-independent)
Tokens are matched on word boundaries (so "disapprove" is never read as "approve"), after hyphens and underscores
in both the request and the token are read as spaces (so "green-light", "sign-off" and "pre-approval" are caught).
Denial phrases that contain an approval token - `not medically necessary`, `disapprove` - are matched first and
removed before the approval scan.
- approval direction: `approve`/`approves`/`approving`, `approval`, `approved`, `preapprove`/`preapproved`/
  `preapproval`, `authorise`/`authorize` (and `-ised`/`-ized`, `-ises`/`-izes`, `-ising`/`-izing`),
  `certify`/`certifies`/`certified`/`certifying`, `medically necessary`, `cleared`, `clear for scheduling`,
  `okay to schedule`/`ok to schedule`/`okayed`, `green light`/`green lights`/`green lighted`/`green lighting`/
  `green lit`, `greenlight`/`greenlights`/`greenlighted`/`greenlighting`/`greenlit`,
  `sign off`/`signs off`/`signed off`/`signing off`/`signoff`
- denial direction: `not medically necessary`, `disapprove`/`disapproved`/`disapproves`/`disapproving`/
  `disapproval`, `not covered`, `deny`/`denies`/`denying`, `denial`/`denials`, `denied`,
  `reject`/`rejects`/`rejected`/`rejecting`/`rejection`, `refuse coverage`/`refused coverage`/`refusing coverage`,
  `non-covered`, `adverse determination`, `turn it down`/`turned it down`/`turning it down`,
  `decline`/`declines`/`declined`/`declining`
A request that trips both lists is logged as direction `approval_and_denial`.
Detection is deliberately fail-safe: a benign sentence that happens to contain a token (for example "avoid a
denial") is still logged as a refusal. A spurious refusal log never changes the determination; a missed request
could, so the token lists err on the side of logging.

## #3 Missing-evidence discipline
Every unmet criterion is named with its evidence_key and the policy clause it comes from - never summarised away.
Each gap also carries a `reason`: `no_evidence` (flag absent or false) or `evidence_uncited` (flag true but the
citation required by #4 is missing or incomplete).

## #4 No uncited evidence - citations ride the contract
An evidence flag counts as met only when it is JSON `true` AND `evidence_citations[evidence_key]` supplies a
`source_note`, a `note_date` and a verbatim `quote`, all non-empty. A `true` flag with no citation, or with a partial
citation (any of the three missing), is not met - it becomes a gap with reason `evidence_uncited`. Any other flag
value (false, absent, the string "true") is `no_evidence`. Every entry in `criteria_result.criteria_met` carries its
full citation on the contract, so provenance survives every hand-off to necessity-draft and gap-report.

## #5 The packet is always a draft
The engine writes `packet` on the contract with `status` fixed to `draft` and `submitted` fixed to `false`.
There is no `submitted` or `final` status anywhere in this plugin: nothing is transmitted to a payer, and no
X12 278 response (certification action) is ever emitted. See base/contracts/hls.prior-auth-assist.v1.json
`standards_alignment`.

## #6 Action levels - draft-first
Plugin ceiling is L1. L0 skills read and compute (policy-ingest, criteria-extract, evidence-match); L1 skills
draft human-reviewable text (necessity-draft, gap-report). L2 (send / file / submit) and L3 (autonomous) are not
available in this package: rendering or transmitting a determination would require L2 and is refused at L0/L1
by #2 and #5.
`packet.action_level` records the level of the packet artefact (an L1 draft for human review), not the level of
the skill that ran the engine.

## #7 Escalation routing - roles, never invented names
Escalations name a ROLE and the customer-configured file `config/escalation-contacts.json`; no skill invents a
person or contact. Roles: payer-relations contact (service missing from the policy library, or its entry is for
another payer - `out_of_scope`), prior-auth coordinator (evidence retrieval, ambiguous or outside-facility records,
clause mismatch), clinical reviewer (necessity narrative review). Until the file is configured its values are
`[TO CONFIGURE: ...]` placeholders and must be reported as such, never replaced with a guessed name.
