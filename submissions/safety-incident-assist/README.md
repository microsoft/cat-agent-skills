# Safety Incident Assist

Turn incident notes into a clear, sourced draft for your safety team to review.
Safety Incident Assist helps organize what happened, where the information came
from, what is still unknown, and who could review it next.

For safety coordinators, shift supervisors, and environmental, health and safety
(EHS) reviewers preparing an incident handoff in Copilot Cowork.

## Picture this

You have an incident report and two witness accounts. One witness mentions a
loose cable in a walkway; another says the walkway was clear. You need a balanced
handoff that gives your reviewer both perspectives.

The plugin is designed to keep both accounts linked to their sources, flag the
disagreement, and leave unanswered questions visible. Both accounts remain
available for your reviewer to assess.

## What you get

A draft incident write-up in Markdown, a plain-text format with headings and
lists, prepared from the completed workflow. It brings together:

- **The incident account:** supplied facts with references back to their sources.
- **Gaps and disagreements:** unknown details and conflicting accounts for review.
- **Draft assessments:** suggested severity and recording classification, or
  "undetermined" where the evidence does not support a conclusion.
- **Proposed routing:** a suggested investigator and recipient list. Your team
  reviews the proposed investigator and recipients before taking action.
- **An investigation worksheet:** a blank root-cause-analysis template, ready
  for your reviewer to explore contributing factors.

Severity is the draft assessment of how serious the incident is. *Recordability*
is the plugin's term for whether the supplied facts support recording an incident
in a safety log.

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
working files between stages. When more information is needed, the plugin
highlights the questions and identifies what to supply next.

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
| 4 | Routing | Proposes an investigator and recipients for your team to review. |
| 5 | Incident write-up | Checks and recomputes the preceding outputs, then creates the draft and blank investigation worksheet. |

The workflow works from the incident files, policies, and history you provide.

## What stays with your safety team

Your safety team owns final assessments, reporting deadlines, equipment decisions,
notifications, filings, approvals, and incident closure. The plugin prepares the
supporting draft for their review.

Working files can retain identifying and medical details from your inputs. Review
and minimize these details before retaining or sharing outputs.

## Technical details

Each skill includes its required contracts, references, and Python runtime
dependencies. The bundled helper scripts run locally using the Python standard
library.

## Contributors

- Copilot Acceleration Team (CAT)
