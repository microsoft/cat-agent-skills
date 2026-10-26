# Audit Readiness

For the quality manager six weeks out from a surveillance audit who needs to know, honestly,
where the gaps are — while there is still time to close them.

It maps the audit scope to the standard's clauses, gathers the evidence register and checks it
for completeness, validates each piece of evidence against what the clause actually requires,
flags every gap with a severity, and drafts the readiness pack with owners and actions.

## How it works

1. Maps the audit scope to the standard's clauses (deterministic).
2. Gathers the evidence register and checks completeness.
3. Validates evidence against clause requirements and grades each gap (deterministic).
4. Drafts the readiness pack with gaps, owners and actions.

The gap check is the core of this plugin, not a wrapper around a document count.

## Example scenario

"We passed last year and the folder is full." Three majors are hiding in the full folder:

- The **management review minutes** are dated more than 13 months before the audit. Stale.
- The **internal audit** covers production and quality — but maintenance just entered scope, and
  has no coverage.
- An **inspector has been active since June with no training record**.

A naive check counts documents and passes. This one checks dates, coverage and people, and
returns *not ready* with three majors, each with an owner and a produce-the-evidence action.

Gaps close with evidence, not with wording. The plugin will not let a gap be written away.

## What you bring

The audit scope and standard, your evidence register, and the underlying records — management
review minutes, internal audit reports, training records, calibration records.

## Boundaries

Draft-first: the output is a readiness pack. Producing the missing evidence is human work, and
the plugin says so rather than papering over it.
