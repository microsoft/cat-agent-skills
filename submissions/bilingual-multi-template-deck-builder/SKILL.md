---
name: bilingual-multi-template-deck-builder
description: "Use when asked to create a new editable English or Hebrew PowerPoint deck from the bundled NOVA WORKS dark or light templates in Cowork, Copilot Studio, or Scout. Use supported native template tools or the bundled Python builder and deliver the actual PPTX."
license: MIT
metadata:
  author: "Ofir Gavish"
  version: "1.1.1"
---
# Bilingual Multi-Template Deck Builder

Created by Ofir Gavish. See LICENSE.txt for redistribution terms. Ordinary
generated presentations do not require creator credit; do not insert it.
NOVA WORKS is a fictional demo brand. Sample figures are synthetic, not evidence.

## Select before building

Use this skill for a NEW presentation, not an in-place edit to an existing deck.
Ask for English or Hebrew, then dark or light, unless explicitly supplied.
Do not infer theme from an open presentation. Ask for the topic, audience, source
facts and desired slide count when missing. Do not invent business results,
dates, owners or commitments; label proposed actions and illustrative data.

| Language | Theme | Template key |
|---|---|---|
| English | Dark | en-dark |
| English | Light | en-light |
| Hebrew | Dark | he-dark |
| Hebrew | Light | he-light |

Resolve the exact asset and layout bindings from `references/templates.json`.
All four PPTX templates are INSIDE this skill at `assets/templates/`; no manual
template attachment, cloud template URL or connector is needed for generation.

## Check the runtime, not the host's name

Read `references/hosts.md` for the current host's setup and delivery contract.
Use only capabilities actually exposed in the session. A recognized host name,
successful skill import or code-interpreter toggle is not proof of execution.
Do not invent tool names, asset locations, probe receipts or download URLs.

1. Locate the actual selected bundled PPTX through the installed skill's
   resources or its host-managed storage metadata. Confirm the file is
   accessible to the tool that will create the presentation, not just readable
   by a separate instruction-viewing tool.
2. Identify a supported output destination and real file-delivery mechanism.
   Obtain required access through the host's normal permission flow.
3. If native presentation tools accept that actual template through a supported
   file reference, use `references/native-workflow.md`. **Python is not required
   for this route**, and no Python probe is needed.
4. Otherwise, try the bundled direct builder only if its prerequisites below
   are available. An isolated Python runtime is not proof of template access,
   just as available presentation tools are not proof of a native handoff.

A host may store imported skill resources in the user's OneDrive. If it exposes
that location and a supported import/copy operation, staging the original bundled
file through that operation is valid. Discover the real file reference from
metadata; do not guess a personal path/URL, search unrelated workplace files,
or require a separately downloaded or manually attached template.

Never bypass sandbox or file-scope restrictions, convert a local path into a
fake attachment URL, or reconstruct the design from screenshots. If neither
route can reach the actual template and deliver the result, state the specific
blocker. A manual attachment/open-copy fallback is not automatic bundled-skill
success. Do not silently substitute generic slides.

## Direct Python route

Use this route only when native template handoff is unavailable or unsuitable
and code execution can access the installed scripts AND selected binary asset.

Confirm Python 3.10+ with `python-pptx>=1.0.2,<2`, `defusedxml>=0.7.1,<1` and
`lxml>=4.9,<7` is already available. The packaged `requirements.txt` is for an
administrator's or developer's approved local setup, not an instruction to
install into a hosted sandbox.

ACTUALLY execute `scripts/build_presentation.py --probe` using the real script
path. Require exit status zero and JSON `ok: true`. This read-only probe checks
dependency availability and template hashes, not file delivery. Do not invent
a probe result for a native-tool run or a missing execution capability.

Read `references/content-format.md`. Write a UTF-8 plan with `language` and
`slides`, using only supported fields and the user's facts. Packaged examples
in `examples/` illustrate six-slide stories and all eight layouts in each
language; never present their synthetic content as the user's facts.

Execute the actual builder, substituting discovered paths and the chosen key:

```text
python "<skill-root>/scripts/build_presentation.py" --template <key> --content "<plan.json>" --output "<new-approved-output.pptx>"
```

Use the host OS's path separators. The strings above are placeholders, not
paths to execute literally. Choose a NEW `.pptx` in an existing approved output
directory outside the skill folder. Never overwrite templates or existing files.

Require exit status zero and the real JSON receipt: `ok: true`, matching
`template_key` and slide count, `source_unchanged: true`, and
`design_parts_preserved: true`. Report errors; never silently drop unsupported
objects or unbound fields. A receipt's local `output` is not a download link.

The shared builder clones complete reference slide compositions and edits
native text, charts and tables. It retains masters, layouts, themes, fonts and
retained media. Repeated chart slides receive independent chart/workbook parts.
It clears omitted optional text and source speaker instructions; include only
user-approved notes. It does not import arbitrary source decks into this schema.

## Preserve design and direction

Keep the selected branding, typography, geometry, logos, palette, footer and
legal notices. Never recreate the template approximately or flatten slides.
Use cover, section, three-cards, metrics, chart, roadmap, table and closing
compositions as appropriate. Split dense content instead of shrinking fonts.
Tables must match the reference's four rows and three columns.

These requirements apply to BOTH generation routes.
For Hebrew, use real RTL paragraphs, right alignment and authored right-to-left
cards/steps. Keep Latin product names, URLs, emails and signed numbers internally
LTR. Never reverse characters or mirror logos. The Python builder handles native
direction; do not run a separate XML rewrite on its output. With native tools,
verify actual paragraph and run direction as well as visual mixed-script spacing.

Inspect the generated slide content and chart/table data. Check for leftover
sample text and notes. Render and inspect for overflow and clipping when a
renderer is actually available; report visual inspection as unverified otherwise.
Referenced fonts are Aptos, Aptos Display and Arial; no font binaries ship.
Font substitution can affect visual fit and must not be hidden.

## Deliver and state what happened

Publish the real output with the host's supported artifact/file mechanism.
For Scout, follow its provider-aware document tools and approved destination;
for hosted agents, return an actual attachment/artifact or a verified file link.
See `references/hosts.md`. Do not upload to OneDrive, SharePoint or another
destination or share with other people without the user's direction/approval.

Return the generation route (native or Python), selected template filename,
language/theme, slide count and actual delivered file/link. If generation
succeeded but publication failed, say delivery is blocked; do not claim the
task completed. Generation creates a new
file, does not update an open PowerPoint canvas, and never implies host
certification. Distinguish performed checks from unverified ones.
