---
name: eligibility-check
description: 'Determines return eligibility against the configured policy and surfaces fraud signals deterministically with the eligibility_check engine - the explicit Govern step of this plugin. Use after reason-classify, or on "is this returnable", "do they qualify for a refund", "check eligibility", "any fraud signals", "can we accept this return". Do NOT use to retrieve policy text - use policy-retrieve instead; not to start a case - use return-intake; not to draft the packet or customer response - use case-packet.'
license: Proprietary
metadata: {version: "1.0.3", author: Microsoft Retail & CPG Skills, category: analysis}
---
# Eligibility Check (Govern)
## Purpose
The compliance determination IS the work: eligible / ineligible / needs_evidence with the clause cited (#2.1), plus fraud signals surfaced - never adjudicated (#3).
## When to use
- After reason-classify in every case; or when asked whether a return qualifies or has red flags.
## When NOT to use
- Fetching policy wording or windows - policy-retrieve.
- Structuring the request - return-intake. Reason coding - reason-classify.
- Writing the packet, customer response or exception request - case-packet.
- Aggregate reporting (return rates, dashboards) - out of scope.
## Inputs
Plugin assets ship inside this skill folder (synced from the plugin-root shared/ copy before packaging): `config/`, `contracts/`, `references/returns-rules.md`, `demo-data/` - paths below are relative to this skill folder.
`classified.json` + config/return-windows.json. Engine: scripts/eligibility_check.py. Schema: contracts/rtl.returns-refund-case.v1.json.
## Steps
1. Validate `classified.json` against the contract (required keys, `contract_version`, `reason` present).
2. Run `python scripts/eligibility_check.py --classified classified.json --config config/return-windows.json --out governed.json`.
3. Quote `determination`, `clause`, `detail`, `missing_evidence` and every `fraud_signals[]` entry verbatim. No order record -> the engine returns `needs_evidence` (RET-1.2) - relay that the lookup must land before any decision.
4. Any fraud signal or confidence < 0.75 -> `hold_for_review`: route to asset protection / manager (#4.1, #4.2). Present signals factually, no accusations.
5. A sympathetic story (tenure, loyalty, "the manager did it last time") is context for a HUMAN exception (#5.1): say so, and hand the exception request to case-packet.
## Example
```
$ python scripts/eligibility_check.py --classified classified.json --config config/return-windows.json --out governed.json
eligibility_check: ineligible (RET-2.1) rec=hold_for_review signals=3 -> governed.json
Reply sections: Determination | Recommendation | Missing evidence | Fraud signals (table: signal | detail | rule | source)
  "Determination: ineligible - RET-2.1 - 32 days since purchase > 15-day electronics window (#1.1).
   Recommendation: hold_for_review (3 signals, #4.2). Signals: serial_mismatch (#3.1), return_frequency (#3.2), high_value_receiptless (#3.3).
   The customer's loyalty story is context for a manager exception (#5.1) - drafted by case-packet, never granted here.
   DRAFT - a human authorises any refund, exchange or decline."
```
## Output format
`governed.json` - payload plus `eligibility: {determination, clause, detail, missing_evidence[], recommendation, confidence, source, citation}` and `fraud_signals[]`. In chat: one line each for determination + clause, recommendation, missing evidence, and a factual signal list; end with "DRAFT - a human authorises any refund, exchange or decline".
## Grounding requirements
Every determination cites its clause and config; every signal cites the record it came from.
## Guardrails
- Never fabricate a determination, clause, confidence or signal; every value is quoted from governed.json and cites its record.
- The engine decides; the model never grants an exception (#5.1), never drops or adds a signal, never softens ineligible to "probably fine", never edits governed.json by hand.
- Never authorise a refund, release funds, approve store credit, or add a customer to any list.
- Never write "fraud", "fraudster" or "confirmed" about a customer - signals are signals.
- Engine error or contract mismatch: stop and report; do not hand-compute a determination.
## Escalation / uncertainty
If the engine fails or the contract does not validate, stop and report - never hand-compute a determination or fabricate a clause. If `order` is missing, relay the engine's needs_evidence (RET-1.2) and name the lookup that must land.
Signals, missing evidence or low confidence -> hold_for_review with the packet routed to asset protection / manager.
