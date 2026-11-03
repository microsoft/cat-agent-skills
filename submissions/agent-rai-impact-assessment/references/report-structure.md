# Assessment report structure

Adapt to the user's existing template. Use short tables or per-harm cards rather than a single unreadably wide register; chat channels such as Teams render wide tables poorly. Keep the assessment marked Draft unless an actual review status is supplied.

Use stable IDs throughout: H-nn for harms, C-nn for controls, T-nn for evaluation gates, Q-nn for open questions.

## 1. Decision brief

State the assessed use/version, lifecycle stage, sensitive-use flag if raised, recommendation, material impacts (by harm ID), evidence limitations, and the decisions required from accountable people. Distinguish a bounded experiment from production release. Record assessment author/reviewer only when supplied.

## 2. Scope and people

Describe intended and unsupported uses, expected benefit, current alternative, and affected parties. For each party, show potential benefit, potential burden, and evidence or consultation still needed. Include non-users when the agent can act on their records or opportunities.

## 3. Agent authority and data boundary

Use a concise table. Example row for a procurement agent:

| Action/path | Effective identity and resource scope | Human decision and enforcement point | Side effect, recovery, evidence |
| --- | --- | --- | --- |
| Submit purchase request via ERP connector | Runs under the buyer's own credentials; limited to the buyer's cost center; amount ceiling set in the connector configuration, not in the instructions | Buyer confirms a card showing vendor, amount, and cost center before the tool runs; requests above the threshold also enter the ERP approval workflow | Side effect: request created in ERP. Recovery: cancel in ERP before approval; no automatic reversal after approval. Evidence: tool configuration export, transcript T-03, ERP log sample |

Include memory, logs, and delegated agents only where present or proposed.

## 4. Harm and control register

Give each material scenario an ID and a card. Example:

**H-01 Duplicate purchase request after tool timeout**

- **Use and affected party:** draft-and-submit purchase requests; buyer, finance approvers, supplier.
- **Chain:** ERP connector times out after the request is created → agent retries the same call → two requests exist → funds committed twice and approvers work both. Consequence type: financial loss, extra review burden.
- **Evidence:** tool contract section 4 shows no idempotency key; no supplied test covers timeout. Status: potential, design-supported; no observed incident.
- **Severity:** Medium, remediable and bounded by the amount ceiling. **Plausibility:** Unknown, no timeout frequency data. **Confidence:** Medium, from design documents only.
- **Controls:** C-01 ERP approval workflow, Evidenced for amounts above the threshold, Claimed below it. C-02 proposed: check for an existing request before retry, or an idempotency key; enforcement point: connector or flow; owner role: integration owner.
- **Gate:** T-01 simulate a timeout after creation; expected: exactly one request and the agent reports an uncertain state to the buyer; proposed pass criterion: zero duplicates across 20 runs, pending reviewer agreement; retain transcripts and ERP log extract.
- **Residual:** expected residual risk Low, contingent on T-01 passing; acceptance not recorded.
- **Open:** Q-01 does the connector return the created request ID on timeout?

Keep unsupported claims in an evidence-gaps list rather than writing them as confirmed incidents. Mark inapplicable areas with a reason if completeness is important to the requested review.

## 5. Evaluation and mitigation backlog

Prioritize by potential harm and decision sensitivity. Trace each item to a harm ID and give a pass condition, owner role, and consequence of failure. Separate test results already supplied from proposed tests.

## 6. Operation, recourse, and review

Describe reporting/correction routes for affected people, monitoring signals, incident ownership, stopping/recovery controls, and reassessment triggers. List outstanding authority, policy, privacy, domain-expert, or legal questions by Q-ID only when relevant to the actual scenario.

## 7. Evidence and sources

List supplied artifacts, assumptions, external sources actually checked and their access dates, and unavailable evidence. Record whether stakeholder participation occurred.
