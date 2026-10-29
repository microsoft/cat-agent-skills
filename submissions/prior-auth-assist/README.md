# Prior Authorization Packet

For utilization management and prior authorization staff preparing a request before it goes to the payer.

It finds the coverage policy that governs the ordered service, checks the chart against each criterion, cites the notes that satisfy it, drafts the medical necessity narrative and lists what is still missing.

The design bet is a complete, cited packet over a fast one: a request that goes out with a gap comes back as a denial.

## How it works

1. **policy-ingest** finds the payer coverage policy that governs the ordered service and records its clause.
2. **criteria-extract** checks the request against that policy clause by clause and reports which criteria are met and which are open.
3. **evidence-match** finds the chart notes, dates and verbatim quotes that back each criterion.
4. **necessity-draft** writes the medical necessity narrative from met, cited criteria only.
5. **gap-report** lists every piece of evidence still missing and presents the packet as a draft for review.

## Try it

- **Check payer criteria:** "Does the patient on order [order id] qualify for [service] under [payer]'s coverage policy? The order and chart notes are in [folder]."
- **Build the prior auth packet:** "Build the prior authorization packet for [service] on order [order id] and write the medical necessity justification from the chart notes in [folder]."
- **Find what is still missing:** "What is still missing on the prior auth for order [order id] before it goes to [payer]?"

## What you bring

The order, clinical notes, imaging and pathology reports, labs, prior authorization history and your payer medical policy library.

Suggested connectors: X12, Salesforce, Box, Oracle Database, Snowflake, ServiceNow and Adobe PDF Services.

## Before you use it

Each skill has a `config/` folder with settings marked `[TO CONFIGURE]`. Fill these in for your organisation; until you do, the skills report the item as not routed rather than guessing.

- `payer-policy-library.json`: your payer coverage policies and their criteria.
- `escalation-contacts.json`: who to route clinical, payer and compliance questions to.

## Boundaries

Draft packets and gap reports for human review. It never approves, denies or submits a prior authorization request.

Outputs are drafts that support, not replace, clinical and professional judgement. Use synthetic or de-identified data when trying it out.
