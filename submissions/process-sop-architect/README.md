# Process & SOP Architect

Turn workshop notes, interviews, meeting transcripts, requirements, or an existing procedure into a complete and reusable process documentation package.

Process & SOP Architect helps teams move from scattered process knowledge to a validated operating model. It separates confirmed facts from assumptions, asks targeted questions when essential details are missing, and produces editable deliverables for frontline teams, project leaders, process-improvement practitioners, auditors, and executives.

## What it creates

From one structured process specification, the skill can generate:

- An editable Microsoft Word SOP
- An SVG process map that can be opened in a browser or inserted into Office
- An Excel RACI matrix and control register
- A CSV improvement backlog
- A Markdown executive summary and unresolved-question log
- An editable, polished PowerPoint executive briefing

The PowerPoint briefing includes an executive snapshot, process flow, roles and handoffs, controls and risks, improvement roadmap, visual metrics, and next steps.

## Before you start

Provide source material that describes the process, such as:

- Workshop or interview notes
- A meeting transcript
- An existing SOP or policy
- Process requirements
- A list of activities, systems, roles, controls, and known issues

For best results, identify whether you want the **current state**, **future state**, or **both**.

The packaged generators use these Python libraries:

- `python-docx`
- `openpyxl`
- `python-pptx`

In the Copilot Studio sandbox these libraries are already available, so no installation is needed. Only when you run the scripts **outside** Copilot Studio (for example, local testing) do you need to install them first:

```bash
pip install python-docx openpyxl python-pptx
```

## How to use it

Attach or paste your source material and ask the agent to use Process & SOP Architect.

### Example: document a current-state process

> Use Process & SOP Architect to document the current-state vendor onboarding process from the attached workshop transcript. Ask one question at a time for essential missing information. Generate the SOP, process map, RACI and control workbook, improvement backlog, executive summary, and PowerPoint briefing. Do not invent owners, controls, policies, or service levels.

### Example: design a future-state process

> Analyze these notes and create a future-state employee onboarding process. Clearly separate current pain points from proposed improvements. Include decision paths, exceptions, controls, role handoffs, adoption risks, and an executive PowerPoint presentation.

### Example: improve an existing SOP

> Review the attached SOP using Process & SOP Architect. Identify unclear ownership, missing controls, incomplete exception handling, and process gaps. Create an improved SOP and a leadership presentation explaining the recommended changes.

## How it works

The skill:

1. Reviews the supplied source material.
2. Establishes the process boundary, trigger, outcome, roles, systems, decisions, exceptions, controls, and measures.
3. Marks unresolved information as `TBD` rather than inventing details.
4. Creates a structured process specification.
5. Validates ownership, decision paths, references, and control evidence.
6. Generates the full process documentation package.
7. Reviews the outputs for traceability, usability, and unsupported claims.

## Customizing the PowerPoint

The presentation generator uses:

```text
assets/presentation_theme.json
```

Update this file to apply your preferred colors, fonts, and presentation styling. The generated slides remain editable in Microsoft PowerPoint.

## Good to know

- The quality of the outputs depends on the completeness and accuracy of the source material.
- Missing owners, dates, controls, and policies are labeled as unresolved rather than assumed.
- Recommendations are kept separate from confirmed current-state facts.
- Complex processes may be easier to document as multiple linked subprocesses.
- The SVG process map is designed for clear business-process communication; it is not intended to replace a full BPMN modeling application.
- Generated documents should be reviewed by the appropriate process owner, compliance team, or subject-matter expert before formal approval or publication.
- The skill does not introduce unsupported policies, regulatory interpretations, or organizational commitments.

## Sample outputs

A typical process package contains files similar to:

```text
vendor_onboarding_sop.docx
vendor_onboarding_process_map.svg
vendor_onboarding_raci_and_controls.xlsx
vendor_onboarding_improvement_backlog.csv
vendor_onboarding_summary.md
vendor_onboarding_executive_process_briefing.pptx
```
