# Returns & Refund Case

For the service desk or contact-centre agent making a return decision that is genuinely a
compliance determination — and needs to be the same decision whoever is on shift.

It structures the return request against the order, receipt, SKU attributes and customer
return history, attaches the applicable return-policy clauses verbatim, classifies the return
reason against the taxonomy, validates eligibility deterministically with the policy clause
cited, surfaces fraud signals from a rule set without adjudicating them, and drafts the
recommendation and case packet.

Governance is an explicit step here, not a platform guardrail: the refusal has to be
defensible.

## How it works

| # | Skill | Job |
|---|-------|-----|
| 1 | `return-intake` | Structures the request: item, order/receipt, reason as stated, condition, serials, return history |
| 2 | `policy-retrieve` | Attaches the applicable return-policy clauses and configured windows, verbatim |
| 3 | `reason-classify` | Classifies the return reason against the taxonomy (deterministic engine) |
| 4 | `eligibility-check` | Determines eligibility with the clause cited and surfaces fraud signals — the Govern step |
| 5 | `case-packet` | Drafts the recommendation, customer response and case packet |

## The case that shows why it exists

Loud, sympathetic, urgent — and every record says hold:

- **32 days against a 15-day electronics window** — ineligible, with the clause cited.
- The **serial on the unit does not match the serial sold** on that order — surfaced as a
  signal, not adjudicated.
- It is the **fourth receiptless return in 90 days**, above the value threshold.

The determination is ineligible, the recommendation is hold-for-review, the packet routes to
asset protection, and the manager exception is *drafted as a request* — the plugin never
grants it. A naive agent processes the goodwill refund to end the scene.
