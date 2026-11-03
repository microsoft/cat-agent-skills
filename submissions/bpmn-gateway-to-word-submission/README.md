# BPMN to Word Process Documentation

Give the agent a BPMN diagram and get back a Word document that walks through the
process one numbered step at a time.

## What you need

- A BPMN diagram as either:
  - a **`.bpmn` / `.xml` file** (BPMN 2.0 XML): exact and preferred, or
  - an **`.svg` exported from bpmn-js** (for example, export as SVG from Camunda
    Modeler or the bpmn.io editor). SVGs from other tools are not supported.
- An agent environment with Python 3 and `python-docx`. The scripts use only the
  standard library otherwise, and need no network access.

## Try it

Upload `assets/sample.bpmn` (a customer-onboarding process with a decision, a
loop, three parallel pathways and a Link connector pair) and ask:

> Document this BPMN process step by step in a Word document.

## What you get

- One numbered step per task, event, and branching gateway.
- Every branch states where it goes (`If "Yes": Step 4`, `Loops back to Step 8`).
- Each parallel (AND) fork written out as full Pathway A / B / C sections, then a
  join callout saying where the process resumes. Nested forks are handled.
- Lane names as Performer, text annotations as Notes.
- An "Items to confirm" section listing anything the parser could not resolve.

## How it stays accurate

The extraction is done by scripts, not by reading the picture. For XML it reads
`sourceRef`/`targetRef` directly. For SVG it rebuilds connections from shape
geometry, then fails loudly (exit code 2) if the result looks wrong, rather than
producing a plausible but incorrect document.

## Limits

Sub-processes are flattened; OR, event-based and complex gateways are written as
plain decisions; boundary events and event types come through only from XML.
