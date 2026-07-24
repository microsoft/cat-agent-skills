---
name: process-sop-architect
description: Use this skill whenever the user asks to document, map, standardize, redesign, or improve a business process from notes, transcripts, interviews, or requirements, especially when they need an editable SOP, process map, RACI, controls, improvement backlog, or polished PowerPoint briefing.
---

# Process & SOP Architect

## When to activate this skill
Activate when the user asks to document, map, redesign, standardize, or improve a business process. Typical triggers include: "turn these notes into an SOP", "map our onboarding process", "create a RACI", "document the current state", "identify process gaps", or "create a future-state workflow".

Do NOT activate when:
- The user wants a software architecture diagram rather than a business process.
- The request is only to summarize a meeting without building an operating procedure.
- The user has not supplied enough information to identify the process scope and actors.

## How this skill runs
1. Review the user's source material and build a process specification using `references/process_spec_schema.md`.
2. Ask targeted questions for missing trigger, scope, roles, decisions, exceptions, controls, or outputs. Ask one question at a time.
3. From the skill's root directory (the folder that contains `scripts/` and `references/`), save the specification as `process_spec.json`, and run the commands below from that same directory so the `scripts/` paths resolve. Use this directory rather than `/tmp`, which is not reliably writable in the sandbox.
4. Validate it:
   ```bash
   python scripts/validate_process_spec.py --input process_spec.json
   ```
5. Generate the process pack, including the polished executive PowerPoint briefing:
   ```bash
   python scripts/generate_process_pack.py \
      --input process_spec.json \
      --output-dir process_pack
   ```
6. Return the generated SOP, process map, RACI workbook, improvement backlog, executive summary, and PowerPoint briefing.

## Requirements
- `python-docx` (Word SOP)
- `openpyxl` (Excel RACI and control register)
- `python-pptx` (PowerPoint executive briefing)

These packages are present in the Copilot Studio sandbox — no `pip install` is required. The generators import them at startup and fail fast with a clear error if a dependency is missing, so a partial pack is never reported as complete.

## Required outputs
- Editable Word SOP
- SVG process flow that can be opened in a browser or inserted into Office
- Excel RACI and control register
- CSV improvement backlog
- Markdown executive summary and unresolved-question log
- Editable PowerPoint executive briefing with title slide, snapshot, process flow, role handoffs, controls, risks, roadmap, chart, and next steps

## Workflow the agent must follow
1. Establish whether the user wants current state, future state, or both.
2. Define the process boundary: trigger, start, end, inputs, outputs, and exclusions.
3. Identify roles, systems, decisions, handoffs, exceptions, controls, and evidence.
4. Separate observed facts from assumptions and recommendations.
5. Build a complete process specification.
6. Run validation and resolve errors before generation.
7. Review generated deliverables for traceability and usability.
8. Ensure the PowerPoint uses assertion-style slide titles, separates facts from recommendations, and does not introduce unsupported claims.

## Quality rules
- Use verb-object wording for process steps, such as `Validate request` or `Approve payment`.
- Every step must have an owner.
- Every decision must define both yes and no paths.
- Every control must identify purpose, owner, frequency, and evidence.
- Do not invent policy, legal, regulatory, service-level, or approval requirements.
- Label missing information as `TBD` and include it in the unresolved-question log.
- Distinguish current-state problems from future-state recommendations.
- Do not automate a process merely because automation is possible.
- The presentation must summarize the SOP; it must not replace the SOP or invent new process facts.
- PowerPoint slides should be leadership-ready, concise, and editable.

## Activation examples
- "Create an SOP from this onboarding workshop transcript."
- "Map the complaint-management process and identify control gaps."
- "Turn these process notes into a RACI and future-state improvement plan."
- "Document our invoice exception process for training and audit."

## Run example
```bash
python scripts/validate_process_spec.py --input assets/example_process_spec.json
python scripts/generate_process_pack.py \
  --input assets/example_process_spec.json \
  --output-dir vendor_onboarding_pack

# Generate only the PowerPoint briefing
python scripts/generate_presentation.py \
  --input assets/example_process_spec.json \
  --output-dir vendor_onboarding_pack
```
