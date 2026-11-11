# Safety Incident Assist

Prepare evidence-grounded incident drafts for a qualified environmental, health
and safety (EHS) reviewer. The plugin works with authorized, user-supplied local
files and keeps missing facts, conflicting accounts, citations, and review holds
visible throughout the workflow.

## Release status

This is source candidate **2.0.0-rc.7**, not a stable or certified release. The
Microsoft 365 app manifest uses numeric version `2.0.0` for packaging
compatibility only; it does not promote the candidate to a stable release.
Native Cowork routing and model extraction still require independent evaluation.

## What's included

- **Incident intake:** preserve cited incident facts and conflicting accounts
  using the bundled v2 contract.
- **EHS knowledge retrieval:** attach supplied local policies and evidence, and
  match prior incidents from a supplied log.
- **Severity and recordability:** run the local deterministic engine to prepare
  draft classification recommendations, retaining undetermined results.
- **Routing:** propose an investigator and unsent recipient list for review.
- **Incident write-up:** revalidate and recompute the workflow outputs, then
  render a cited Markdown draft and a blank root-cause-analysis template.

Each skill includes its required contracts, references, and Python runtime
dependencies. The helper scripts use the Python standard library; they do not
install packages or use network connectors.

## Install

Download the plugin ZIP from this gallery and add it as a plugin in Copilot
Cowork. Keep the package structure intact: the manifest, icons, five skill
folders, and their nested runtime dependencies belong together.

## Before you start

Use an organization-approved environment and only files you are authorized to
process. Supply the incident account and relevant local evidence, such as
witness accounts, applicable policies, job hazard analyses, and a prior-incident
log. Facts that establish applicability or treatment must be explicitly supplied
and cited; missing information is not a negative finding.

Minimize identifying and medical details before processing and at every handoff.
Intermediate JSON and free text are not automatically de-identified. A qualified
EHS reviewer must independently review the evidence and every draft output.

## Try it

"Prepare a cited incident draft from these authorized files. Preserve conflicting
accounts, leave unknown facts undetermined, and propose routing without sending
anything."

## Limitations

Draft preparation only. The plugin does not make official regulatory or clinical
determinations, establish reporting deadlines, issue equipment instructions,
send notifications, file reports, or authorize closure or operational actions.
It has no live retrieval or authenticated approval workflow. Bundled policy and
standards references do not replace the organization's applicable requirements
or qualified human review.

## Contributors

- Microsoft
