---
name: Whiteboard to Infographic
description: "Turn a photo of a hand-drawn whiteboard or process sketch into a polished, client-ready infographic slide (.pptx), generated natively in the agent's Python container."
agentDescription: "Convert a hand-drawn whiteboard photo (or sketched process/diagram) from a discovery or working session into a polished, client-ready infographic as an editable PowerPoint slide (.pptx). Use this whenever someone uploads or references a photo of a whiteboard, a hand sketch of a process or system, or session-capture notes and wants it \"cleaned up\", \"made presentable\", \"turned into a diagram/infographic\", \"converted for the client\", or similar — even if they don't say the word \"infographic\". Covers two layout archetypes — linear process flows (left-to-right step rails) and network/topology maps (locations, systems, or actors connected by labeled flows). Built for consulting/ERP discovery capture but works for any whiteboard-to-deliverable conversion. Do NOT use for charts/graphs from numeric data, for editing an existing polished design, or for generating diagrams with no source sketch."
platforms: [Copilot Studio]
tags: [infographic, whiteboard, powerpoint, presentations, diagrams, design, consulting]
author: Andy Zehr
authorUrl: "https://www.linkedin.com/in/andyzehr"
authorGithub: NickBurns42
version: 1.0.0
createdAt: 2026-07-22
updatedAt: 2026-07-22
bundle: bundles/whiteboard-to-infographic.zip
---
# Whiteboard to Infographic

Turn a messy hand-drawn capture into a clean, branded one-page infographic —
delivered as a single **editable PowerPoint slide** — that a consultant can put
in front of a client. The hard, non-delegable work is reading the handwriting
correctly and choosing the right structure; the styling and layout are codified
here so every output looks consistent.

## The discipline (do this in order — do not skip ahead to styling)

This is structure-first. Producing a polished deliverable from a misread sketch
is the main failure mode, so confirm interpretation **before** building.

1. **Read the source carefully.** The photo is the source of truth. Zoom and
   crop aggressively — examine the image, then crop it into regions and
   re-examine at 2–3x so the handwriting is legible. Transcribe every box,
   label, arrow, annotation, and margin note. Do not silently drop anything you
   can't read — list it as a question.

2. **Confirm interpretation and lock structure.** Before building the slide,
   send the user a compact transcription: the nodes/steps, the
   connections/flows, and any side notes or requirements. Explicitly flag:
   ambiguous words, unexpanded acronyms, and anything you're inferring. Ask the
   questions that change the build (see "Questions to ask"). Wait for
   confirmation. Build only what's on the board — never invent steps, fields, or
   connections to make it look complete. If a relationship isn't drawn, don't
   draw it.

3. **Get the color palette.** The palette is client-specific and is NOT baked
   into this skill. If the user gave colors in the prompt or context, use them.
   Otherwise, ask before building. You need hex values for these roles:
   - **ink** — primary structure, dark text, node borders (e.g. a deep navy)
   - **secondary** — sub-heads, connectors, region boundaries (e.g. steel blue)
   - **accent** — sequence numbers, bullets, flags, emphasis (e.g. a signal red)
   - **card** — light fill for callout cards / cluster fills (e.g. pale blue-gray)
   - **accent-tint** — light wash behind accent-flagged items (e.g. pale red)
   Derive sensible text tints (e.g. a muted slate for sub-captions) from these.
   Offer to suggest a palette if the user has no preference, but don't assume.

4. **Choose the archetype** (state your choice and why):
   - **Process rail** — the sketch is a sequence/flow with a clear order
     (step 1 → step 2 → …). Read `references/process-rail.md`.
   - **Network map** — the sketch is locations/systems/actors connected by
     flows, with no single linear order (a topology). Read
     `references/network-map.md`.
   If it's genuinely both, lead with the dominant reading and ask.

5. **Build, verify, iterate.** Build the slide with `python-pptx` per the chosen
   archetype's reference. The layout is deterministic — **code decides every
   coordinate** — so verify structurally rather than by eye: every step/node
   present, columns/nodes evenly spaced, no shape overlapping another, every
   label inside its box, drop-lines landing on their cards, edges approaching
   nodes straight-on and not crossing through them. If your runtime can
   rasterize the slide, optionally do a visual critique pass; if it can't, lean
   entirely on the computed geometry. Fix in code and rebuild. Faithfulness 
   beats polish — never add a step, field, or connection that wasn't on the 
   board.

## Building the slide (native python-pptx)

Build the infographic as a **single editable slide** with `python-pptx`, drawn
natively as shapes — no HTML, no image rendering, no external render step. It
runs inside the agent's Python container and returns a `.pptx` the client can
open and edit.

The layout is **deterministic — code decides every coordinate.** Design on a
fixed 1600×1000 grid mapped to a 13.333in slide (see each reference for the
`PX()` scale helper), and compute every position from the step/node count and
the canvas so the slide is correct by construction. Use the house-style system
fonts (`Arial Narrow` for condensed display, `Arial` for body) so nothing
depends on font downloads. Turn off the default autoshape shadow
(`shape.shadow.inherit = False`) for the flat house look. Save the deck and
return the single `.pptx` as the deliverable — no PNG/PDF/HTML side-artifacts.

**Revisions: never reuse a filename.** When the user asks for changes to an
infographic you have already delivered, build the revision as a **new file with
a new name** — `infographic-v1.pptx`, `infographic-v2.pptx`, `infographic-v3.pptx`,
and so on — incrementing on every subsequent revision for the life of the
conversation. Do not overwrite, re-save, or re-deliver an existing filename: a
reused name can prevent the updated file from reaching the user, who then
receives the earlier version or no file at all. One revision, one new filename,
every time.

## Conventions (shared by both archetypes)

These are the house style. Keep them consistent across a client engagement.

- **Header band**: condensed uppercase title + a thin small-caps subtitle, a
  full-width accent rule under it, and an optional right-aligned scope/context
  note. A short eyebrow label (e.g. "THE PROCESS", "SUPPLY NETWORK") sits above
  each major band.
- **Accent flags** encode meaning — don't decorate with them:
  - A solid **accent "GAP" pill** marks a gap between the standard system and the
    client's process (a fit/gap item). Use only where the user confirms a gap.
  - A hollow **"need details" tag** marks an open item to define in follow-up.
  - Include a one-line legend explaining any flag you use.
- **Faithfulness**: behaviors/notes with no home in the visual go in a list, not
  invented shapes. Keep the client's exact terms and acronyms; don't expand or
  rename acronyms the client already knows unless asked.
- **Restraint**: spend boldness on one signature device (the numbered chevron
  rail, or the region cluster), keep everything else quiet. Whitespace where the
  source is sparse is honest — don't pad it with invented detail.

## Questions to ask before building

Ask only the ones that actually change the build; don't interrogate.
- Unreadable words / unexpanded acronyms (transcribe what you can, ask the rest).
- Archetype if ambiguous (rail vs. map).
- For a rail: is there a meaningful sequence number/priority on any step? What
  goes in the bottom band — principles, requirements, or nothing?
- For a map: which connections must be explicit vs. summarized in a legend;
  what each node/edge label means; does anything apply across all nodes.
- Whether a "detailed" companion version is wanted (dense capture of every
  margin note) in addition to a clean executive version.
- The color palette, if not already provided.

## References

- `references/process-rail.md` — linear flow archetype: deterministic banded
  layout (header, numbered chevron rail with drop-lines, callout cards,
  principles/requirements bottom band), as a `python-pptx` skeleton with color
  placeholders.
- `references/network-map.md` — topology archetype: node/edge/cluster helpers
  (labeled edges with arrowheads, dashed region clusters, edge-label chips, flow
  legend, requirements band), as a `python-pptx` skeleton with color
  placeholders.