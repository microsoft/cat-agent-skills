# Returns & Refund Case

For the service desk or contact-centre agent making a return decision that is genuinely a
compliance determination — and needs to be the same decision whoever is on shift.

It retrieves the order, receipt, SKU attributes and warranty, classifies the return reason
against the taxonomy, validates eligibility deterministically with the policy clause cited,
surfaces fraud signals from a rule set without adjudicating them, and drafts the
recommendation and case packet.

Governance is an explicit step here, not a platform guardrail: the refusal has to be
defensible.

## How it works

1. Reads the order, receipt, SKU attributes and warranty.
2. Retrieves the applicable return and warranty policy.
3. Classifies the return reason against the taxonomy.
4. Validates eligibility with the clause cited — the Govern step.
5. Drafts the recommendation and the case packet.

## Example scenario

Loud, sympathetic, urgent — and every record says hold:

- **32 days against a 15-day electronics window** — ineligible, with the clause cited.
- The **serial on the unit does not match the serial sold** on that order — surfaced as a
  signal, not adjudicated.
- It is the **fourth receiptless return in 90 days**, above the value threshold.

The determination is ineligible, the recommendation is hold-for-review, the packet routes to
asset protection, and the manager exception is *drafted as a request* — the plugin never
grants it. A naive agent processes the goodwill refund to end the scene.

## What you bring

Return and warranty policy, receipts and order records, SKU attributes and serial data, your
reason-code taxonomy, carrier and RMA rules, and your fraud rule set.

## Boundaries

Draft-first. It never authorises a refund, releases funds, adjudicates fraud, disposes
inventory or books a carrier.
