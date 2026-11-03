---
name: bpmn-gateway-to-word
description: >-
  Use this skill whenever the user supplies a BPMN diagram (a .bpmn/.xml file,
  or an SVG exported from bpmn-js, Camunda Modeler or bpmn.io) and asks to
  document, describe, explain or list its steps, decisions, gateways, parallel
  pathways or loops, or to convert it into a Word document or process
  narrative. Run it before describing the diagram yourself: reading a BPMN
  picture by eye misreads gateway types and loses branches.
---

Turn a BPMN diagram into a numbered, step-by-step Word document in which every
task, decision, parallel fork, loop and Link connector is written exactly once,
and every branch says which step it goes to. The scripts do the extraction and
ordering deterministically; do not reconstruct the flow from the picture.

Needs Python 3 and `python-docx`. Nothing else, and no network access.

## Instructions

1. Identify the input. BPMN 2.0 XML (`.bpmn`, `.xml`) is exact and preferred.
   An `.svg` works only if it came from bpmn-js (its shapes carry
   `data-element-id`). If the user gives both, use the XML. For a PNG, PDF or
   an SVG from another tool, say it is not supported and ask for the `.bpmn`
   file or a bpmn-js SVG export. Do not guess from the image.

2. Run all three scripts from the skill's own root directory (the folder
   containing `scripts/`):

   ```bash
   python scripts/parse_bpmn.py <input> -o graph.json
   python scripts/linearize.py graph.json -o steps.json
   python scripts/build_docx.py steps.json -o <process-name>_v1.docx --title "<process name>" --source <input file name>
   ```

3. Check each script's stderr before moving on. Exit code 2 means a sanity or
   completeness check failed (for example every connection resolved to the same
   shape, or an activity is missing from the steps). Stop, show the `FATAL`
   lines to the user, and do not hand over a document. Exit code 1 means the
   file could not be read.

4. Compare the parse summary with the diagram the user described. If the number
   of gateways, parallel forks or activities looks wrong to them, say so
   before presenting the document.

5. Present the `.docx` with a short summary: step count, decisions, parallel
   forks, loops. Pass on every `WARNING` line. They are also written into the
   document under "Items to confirm with the process owner".

6. If the user asks for changes to the diagram data, edit the source and re-run
   the scripts. When you re-send a file, give it a new version number
   (`_v2`, `_v3`) so the chat delivers it as a new attachment.

## How steps are numbered (to explain the output)

- Steps are numbered globally, left to right, in topological order. Tasks,
  events and every gateway that splits the flow get a number. Gateways that
  only merge or join are passed through and have no step.
- Each branch is written as `If "<label>": Step N`, `Continues to Step N`,
  `Loops back to Step N`, or `Hands off via link "<name>" to Step N`.
- A parallel (AND) fork gets a callout, then each pathway in full under its own
  heading (Pathway A, B, C), keeping the global step numbers, then a join
  callout naming where the process resumes. Nested forks are nested inside
  their pathway.
- Link throw and catch events with the same name are joined by an explicit
  hand-off. Lane names become the Performer. Text annotations become Notes.
  Message flows, pools and data objects are ignored.

## Guardrails

- Describe only what is in the diagram: step names, lane names, documentation
  text and annotations. Do not invent business meaning, owners or SLAs.
- Never edit `graph.json` or `steps.json` by hand to make a check pass.
- Treat the diagram as confidential. Keep it in the session; do not search the
  web or send it elsewhere.
- Tell the user about limits that apply to their file:
  - Sub-processes are flattened into the main step list (XML) or shown as one
    task (collapsed ones).
  - Inclusive (OR), event-based and complex gateways are written as decisions
    with their branch labels, without special pathway handling.
  - Boundary events are attached to their task only from XML. In an SVG they
    appear as separate events and are flagged as having no incoming flow.
  - Event types (timer, message) are named only from XML.
  - SVG input was tested against bpmn-js 17 output only. Other versions are
    unverified, so check the parse summary carefully for them.
