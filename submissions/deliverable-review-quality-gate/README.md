# Deliverable Quality Gate

For engagement managers, partners and quality and risk management (QRM) reviewers checking a client deliverable before it is issued.

It maps each assertion in the draft to the support pack, retrieves the quality-gate criteria and required language, runs the release gates, ranks the findings by severity and drafts a partner review packet that cites every finding.

The design bet is that an unsupported claim is cheaper to catch at the gate than after the client relies on it: anything the evidence does not back is held, not smoothed over.

## What's included

1. **deliverable-ingest** structures the draft deliverable, recipients, evidence index, registers and prior review notes for the gate.
2. **criteria-retrieve** loads the applicable quality framework, gate criteria, required language, brand rules and prior-review findings.
3. **assertion-map** maps each assertion to the support pack and reports whether it is supported.
4. **gate-check** runs the release gates, ranks findings by severity and lists every release blocker.
5. **review-packet** drafts the partner and QRM review packet from the gate results, marked as a draft for human review.

## Before you start

The draft deliverable, its intended recipients, the support pack or evidence index, any registers that feed the gates and prior review notes. No connectors are required; supply the files directly or point to them in SharePoint or OneDrive.

The quality-gate criteria and severity rules bundled in each skill's `references/` folder are illustrative summaries for trying it out, not a real firm's standards. Replace them with your firm's own criteria before relying on the output.

## Try it

- **Start a review:** "Review the draft deliverable in [folder] against its support pack and tell me which assertions lack evidence."
- **Check release readiness:** "Run the quality gate on the [client] [deliverable] and list everything that blocks client issue."
- **Draft the packet:** "Draft the partner review packet for the [deliverable] with every finding ranked and cited."

## Limitations

Draft review packets and findings for a human reviewer. It never signs off, approves client issue, authorizes reliance or sends anything.

Outputs are drafts that support, not replace, professional judgement. Use synthetic or anonymised engagement data when trying it out.

## Contributors

- Copilot Acceleration Team (CAT)
