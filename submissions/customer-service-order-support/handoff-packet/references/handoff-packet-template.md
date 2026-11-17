# Tier 2 Handoff Packet - template (handoff-packet, service-rules.md #4.1)

STATUS: RECOMMENDATION ONLY - human decides; nothing sent, credited, refunded or excepted.
Case: <order id> / <customer id> / channel <chat|email|voice>

## 1. Intent + confidence
- <intent.category>, <intent.confidence> vs floor 0.75 (intent taxonomy, config/service-config.json; service-rules.md #1.1)
- Handoff reason(s): <below floor | contradiction | no approved answer | money-boundary request>

## 2. Consolidated context
| Fact | Value | Source |
|---|---|---|
| Order | <id, value, status, eta> | <OMS export file name>, row n (context.order) |
| Carrier | <status, last scan / delivered_on, location> | <carrier export file name>, row n (context.carrier) |
| Loyalty | <tier> | <loyalty export file name>, row n (context.loyalty) |
| Customer account | "<verbatim inquiry text>" | <customer contact file name> (inquiry.text) |

## 3. Contradiction flags
- <context.contradictions[i] verbatim, including the carrier scan reference> -> DNR path (#2.1). Customer's account is NOT disputed (#2.2).
- (none) if the list is empty.

## 4. Already checked
- Intent classification (engine, citation) · order / carrier / loyalty lookups · contradiction scan (#2.1)
- Instant-resolution gate: tier <x> vs <min_tier>, value <v> vs <max_value> -> <met | NOT met> (SVC-DNR-2)
- goodwill_eligible = false (#3.1) · knowledge status <grounded | no_approved_answer | n/a>
- NOT done by this run: refund, credit, payment change, exception, sends

## 5. Recommended next step (owner: tier 2 human)
1. <policy action, e.g. open carrier investigation SVC-DNR-2, 3-business-day clock>
2. <decision the human makes on the outcome, e.g. refund vs replacement>

## 6. Proposals for human decision
- Goodwill: PROPOSAL - not committed, not promised to the customer (#3.1). Requested by: <customer | agent>, suggested amount: <none | n>.

## 7. Interim customer reply (DRAFT - not sent; agent reviews before sending)
> <Empathetic acknowledgement. What the records show, stated without disputing the customer. The process and the clock. What happens next and who follows up. No refund, credit or date promised.>

## 8. Out of scope / not actioned
- <requests the run declined and why, with rule citations>
