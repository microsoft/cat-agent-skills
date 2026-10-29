# Denials & Appeals Response

For revenue cycle and denials management teams working a denied claim from the remittance to the appeal.

It classifies the denial and its reason codes, attaches the governing payer policy and chart evidence, ranks the queue by deadline then recoverable value and drafts the appeal at the right level.

The design bet is integrity over recovery: an appeal is only as strong as the chart behind it, and a missed deadline cannot be appealed at all.

## How it works

1. **denial-classify** parses the denial letter or X12 835 remittance into denial type, CARC and RARC codes, amounts and appeal level, each cited.
2. **policy-retrieve** pulls the governing payer policy clause, contract term and coding guidance, or reports that none was found.
3. **evidence-assemble** gathers and cites the chart evidence that answers the denial reason and names the gaps.
4. **deadline-track** calculates appeal deadlines, flags urgent and expired claims and ranks the queue by deadline then recoverable value.
5. **appeal-draft** drafts the level-appropriate appeal letter from the cited policy and evidence.

## Try it

- **Classify a denial:** "Classify the denial on claim [claim id]. The remittance advice and denial work queue export are in [folder]."
- **Rank the denial queue:** "Which denials do we work first? Rank the claims in [work queue export] by appeal deadline and recoverable value."
- **Draft the appeal:** "Draft the appeal for claim [claim id] against [payer]'s [policy id] using the chart notes in [folder]."

## What you bring

Denial letters or X12 835 remittances, the original claim, the denial work queue, chart notes and your payer policy and contract library.

Suggested connectors: X12, Salesforce, Oracle Database, Snowflake, SAP, ServiceNow, Box and Adobe PDF Services.

## Before you use it

Each skill has a `config/` folder with settings marked `[TO CONFIGURE]`. Fill these in for your organisation; until you do, the skills report the item as not routed rather than guessing.

- `payer-appeal-windows.json`: appeal windows and levels for each payer.
- The payer policy library and clinical record source named in the skills.

## Boundaries

Classifications, ranked queues and draft appeals for human review. It never recodes a claim the chart does not support and never submits an appeal.

Outputs are drafts that support, not replace, clinical and professional judgement. Use synthetic or de-identified data when trying it out.
