# CASE-<case_id> — Return Case Packet (TEMPLATE)

Fill every `<...>` slot from the governed payload, the policy text or the config. If a value is not in
any of those sources, write `not on record` — never leave an angle-bracket slot or invent a value.

**STATUS: DRAFT — no refund, exchange, exception or decline is authorised by this packet. A human decides.**
**ROUTING: <hold_for_review → Asset Protection | desk lead sign-off>** (returns-rules.md #4.2 / #4.1)

## 0. Leads: escalations and holds
- Escalations: <each escalations[] entry verbatim, or "none">
- Fraud-signal hold (#4.2): <"N signal(s) — hold" | "none">
- Confidence floor (#4.1): <confidence> vs 0.75

## 1. Case facts (each row cites its record)
| Fact | Value | Source |
|---|---|---|
| Case | <case_id> | case.json |
| Item / category / value | <item> / <category> / <value> | return_request |
| Receipt / opened / worn | <has_receipt> / <opened> / <worn> | return_request |
| Order | <order_id>, <order_date>, sold serial <sold_serial> | order (or "no order on record") |
| Unit serial presented | <unit_serial> | return_request |
| Requested on | <requested_on> | return_request |
| Receiptless returns, 90d | <receiptless_returns_90d> | customer_history |
| Reason as stated | "<reason_text>" | return_request (verbatim) |

## 2. Reason code
<reason.category> — confidence <reason.confidence> (engine:reason_classify; config/reason-taxonomy.json).
<If confidence < 0.75: "Ambiguous — confirm with the customer: <alternatives>.">

## 3. Determination
**<DETERMINATION>** — clause **<eligibility.clause>** — "<eligibility.detail>" (<cite rule # and config key/value>).

## 4. Recommendation
<recommendation> (engine:eligibility_check). Awaits human authorisation; this packet does not release funds.

## 5. Missing evidence
<each missing_evidence[] entry, or "none">

## 6. Fraud signals (surfaced, not adjudicated)
| Signal | Detail | Rule | Source |
| <signal> | <detail> | <#3.x> | <citation> |
<or "None surfaced by engine:fraud_signal.">

## 7. Customer response — DRAFT
Tone: courteous, plain, first person, no jargon. State the policy outcome and the clause; state what the
customer can do next (bring the receipt, wait for the manager's decision). NEVER mention fraud signals,
asset protection, or suspicion to the customer. NEVER state processing times, refund timings or amounts
beyond what the policy text or the payload says. If a follow-up contact is needed, write
"we will contact you using the details on your order" — no bracketed placeholders.

> <draft>

## 8. Manager exception request — DRAFT (#5.1) — include only when the customer asked for an exception
Case, determination + clause, what the customer asked for, the customer's stated context (verbatim, not
evaluated), signals present (factual), and a decision block the manager fills in:
Decision: ☐ Declined ☐ Deferred to Asset Protection ☐ Granted — terms: ______  Manager: ______  Date: ______

## 9. Sign-off
Prepared by: <agent/desk> — DRAFT. Authorising human: ______  Date: ______
