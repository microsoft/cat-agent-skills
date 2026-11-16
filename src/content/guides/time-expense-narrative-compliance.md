# Time & Expense Narrative Check

For fee earners and billing coordinators preparing time entries before pre-bill review.

It gathers cited calendar and document activity for an engagement, drafts grounded time-entry narratives, recommends phase and task codes, checks entries against the client's billing guidelines, finds missing time and builds a draft pre-bill exception packet.

The design bet is that a narrative the client rejects costs more than one written carefully the first time: every line is grounded in real activity, and nothing invents roles, attendees or purpose.

## What's included

1. **activity-pull** gathers engagement-scoped calendar metadata, document activity and timesheet rows into a cited activity packet.
2. **narrative-draft** drafts narratives for entries that have none and suggests cited rewrites beside existing ones.
3. **code-map** recommends client phase and task codes and flags mismatches with submitted codes.
4. **guideline-check** checks entries for block billing, prohibited or vague terms, minimum detail, non-billable work, duplicates, increments and unrecorded time.
5. **exception-report** builds the draft pre-bill exception packet of rejects, holds, privacy exclusions and missing time.

## Before you start

The engagement or matter, the billing period, existing timesheet rows, the client's billing guidelines and its phase and task code structure. No connectors are required; supply the files directly or point to them in SharePoint or OneDrive.

`skills/activity-pull/config/signal-sources.json` controls which activity sources the plugin may read. Calendar and engagement-workspace document activity are on by default; mailbox metadata and content are off until your firm approves them.

The billing guidelines and task codes bundled in each skill's `references/` folder are illustrative summaries. Replace them with your clients' actual guidelines and code sets before relying on the output.

## Try it

- **Draft my time:** "Pull my activity for [matter] for the week of [date] and draft my time entries."
- **Check compliance:** "Will these narratives get rejected under [client]'s billing guidelines? Find any missing time too."
- **Prepare pre-bill:** "Show me the pre-bill exceptions for [matter] for [period]."

## Limitations

Draft narratives and pre-bill exception packets for human review. It never submits time, approves a pre-bill, writes off hours or sends anything without explicit confirmation.

Time entries only: expense reports and receipts are out of scope.

Outputs are drafts that support, not replace, professional judgement. Use synthetic or anonymised engagement data when trying it out.

## Contributors

- Copilot Acceleration Team (CAT)
