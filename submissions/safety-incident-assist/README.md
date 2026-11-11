# Safety Incident Assist

Turn incident notes into a clear, sourced draft for your safety team to review.
Safety Incident Assist helps organize what happened, where the information came
from, what is still unknown, and who could review it next.

For safety coordinators, shift supervisors, and environmental, health and safety
(EHS) reviewers preparing an incident handoff in Copilot Cowork.

**Preview: human review required.** This candidate helps prepare drafts; it does
not send notifications, file reports, or approve operational actions.

## Picture this

You have an incident report and two witness accounts. One witness mentions a
loose cable in a walkway; another says the walkway was clear. You need a useful
handoff, not a polished story that quietly chooses one account.

The plugin is designed to keep both accounts linked to their sources, flag the
disagreement, and leave unanswered questions visible. It should not decide which
witness is right or turn the cable into a proven cause.

This is a fictional illustration, not a captured plugin result or supplied
sample-data pack.

## What you get

A draft incident write-up in Markdown, a plain-text format with headings and
lists, prepared from the completed workflow. It brings together:

- **The incident account:** supplied facts with references back to their sources.
- **Gaps and disagreements:** unknown details and conflicting accounts for review.
- **Draft assessments:** suggested severity and recording classification, or
  "undetermined" where the evidence does not support a conclusion.
- **Proposed routing:** a suggested investigator and recipient list. Nobody is
  assigned or notified by the plugin.
- **An investigation worksheet:** a blank root-cause-analysis template to help
  a reviewer investigate why the incident happened, without inventing a cause.

Severity is the draft assessment of how serious the incident is. *Recordability*
is the plugin's term for whether the supplied facts support recording an incident
in a safety log. It is not the same as notifying an authority, and neither is an
official decision here.

## Your first run

1. **Install the plugin.** Download the ZIP from this gallery and add it as a
   plugin in Copilot Cowork. Keep the manifest, icons, five skill folders, and
   their nested dependencies together.
2. **Prepare your files.** Start with a readable incident report, exported email,
   or voice-note transcript that identifies the incident and area or asset.
   Include relevant witness accounts, policies, job hazard analyses (documents
   describing task hazards), and a prior-incident log when available.
3. **Start with the prompt below.** Use fictional information for a first demo.
   For real incidents, use only authorized files in an organization-approved
   environment. Replace unnecessary names and identifiers with aliases first.
4. **Review the draft with a qualified EHS reviewer.** Check the source
   references, unanswered questions, and suggested next steps before using it
   in your organization's process.

You can describe the task in ordinary language; the skills create structured
working files between stages. Missing inputs can prevent later stages from
running. The plugin should ask for them rather than invent a complete report.
Missing information is not evidence that something did not happen.

### Copy and paste

> Prepare an incident draft from these supplied files for EHS review. Start with
> incident intake, then review the supplied policies and history, prepare draft
> assessments, propose routing, and produce the write-up. Link facts to their
> sources, preserve conflicting accounts, and leave unknowns undetermined. If a
> stage needs missing information, stop and tell me what is needed. Do not send,
> file, assign, or close anything.

## How the five skills work together

| Step | Skill | What it does |
| --- | --- | --- |
| 1 | Incident intake | Organizes the supplied incident facts and preserves conflicting accounts. |
| 2 | EHS knowledge retrieval | Uses policies and evidence you supply; looks for related incidents in a supplied log. |
| 3 | Severity and recordability | Runs bundled rules to prepare draft assessments, keeping unsupported conclusions undetermined. |
| 4 | Routing | Suggests an investigator and recipients for review, without assigning or sending. |
| 5 | Incident write-up | Checks and recomputes the preceding outputs, then creates the draft and blank investigation worksheet. |

The workflow uses supplied local files, not live searches or connected business
systems. "Knowledge retrieval" does not mean it can search your organization's
policies unless you provide them.

## What stays with your safety team

The plugin does not make official regulatory or clinical determinations,
establish reporting deadlines, issue equipment instructions, send notifications,
file reports, or authorize closure or operational actions. It has no authenticated
approval workflow. Bundled references do not replace your organization's
applicable requirements or qualified human review.

Keep identifying and medical details to the minimum needed, including in working
files and handoffs. Structured working files (JSON) and free text are **not
automatically de-identified**. A complete draft is not approval to act.

## Release and technical details

This is source candidate **2.0.0-rc.7**, not a stable or certified release. The
Microsoft 365 app manifest uses numeric version `2.0.0` for packaging
compatibility only; it does not promote the candidate to a stable release.
Native Cowork routing and model extraction still require independent evaluation.

Each skill includes its required contracts, references, and Python runtime
dependencies. The helper scripts use the Python standard library; they do not
install packages or use network connectors.

## Contributors

- Copilot Acceleration Team (CAT)
