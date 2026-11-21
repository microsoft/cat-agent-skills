# Native presentation route

Python is an implementation option, not an inherent requirement. Use native
presentation tools when the current host can consume the actual selected bundled
PPTX and preserve its editable design. The presence of a slide-generation tool
alone does not establish that capability.

## Verify the template handoff

1. Resolve the user's explicit language/theme through `templates.json`.
2. Locate that exact bundled file using the host's installed-resource metadata.
   Some hosts store imports in the user's OneDrive; a supported host operation
   may stage the same original file into the task's file area. This is not a
   request to find a different corporate/public template.
3. Obtain the actual resource ID, attachment reference or file handle accepted
   by the native tool. Do not substitute a skill-local path or `file://` URL in
   an attachment-only field. Never invent a cloud URL.
4. Use only a documented/exposed copy or import operation within its allowed
   file scope. Permission/path rejection is a blocker, not a reason to bypass
   the restriction, alter authentication or reconstruct the binary as text.
5. Confirm the operation created a NEW editable presentation from that original
   PPTX. A template name in an instruction, or slides visually resembling it,
   is not evidence that the file was used.

If there is no supported handoff, return to SKILL.md and check whether the direct
Python route can access the COMPLETE bundle: the builder, manifest and all four
template assets at their original relative paths. A successful single-template
native handoff is not proof that this full-bundle Python gate is satisfied.
Removing the Python requirement does not cure missing binary-resource access.

## Populate without approximating

Inspect the copied template with the host's real document tools. Use the
reference-slide indices, unique shape names and field bindings in
`templates.json` to select the authored compositions. Reuse complete native
slide compositions or compatible original layouts; never redraw logos,
generate replacement branding, flatten slides or carry forward sample content.

Use the content fields and density limits in `content-format.md` as the content
contract. Native tools do not have to execute the JSON builder, but must preserve
all supplied facts, chart/table values and intentional notes. Clear omitted
optional example text and inherited speaker instructions.

Copying a template may initially retain its reference/example slides. Keep only
the requested story in the OUTPUT, in the requested order; leave the bundled
source unchanged. Preserve masters, layouts, themes, typography and legal marks.
Do not silently recast charts as images or tables as bullet lists.

For repeated chart slides, verify that each chart has independent editable data
before updating it. If the host cannot safely duplicate/edit a required object,
report that limitation instead of dropping or approximating it.

Hebrew uses genuine paragraph RTL, right alignment, right-to-left card/step
order, and internally LTR Latin names, URLs, emails and signed numbers. Inspect
spaces at Hebrew/Latin boundaries: correctly extracted text alone does not
prove the native rendering is correct.
Keep the supplied characters unchanged while applying direction; do not insert
spaces into hashtags or product prefixes, or include Hebrew prefixes/suffixes
inside an email's LTR token.

## Verify and deliver

Require actual successful copy/import, editing and export results. Verify the
selected source filename, requested slide count, editable content, real
chart/table values, unchanged branding, source preservation and cleared sample
content. Render and inspect when the host supports it. Otherwise state the
unperformed visual checks explicitly.

Return the real editable PPTX artifact or a verified file link using the current
host's supported output mechanism. Do not upload/share with other people or
choose an unapproved cloud destination. A path printed by a tool is not delivery.

Report `native` as the generation route and cite the actual tool results. Do not
claim the Python probe/builder ran or fabricate their JSON receipts. If export or
publication fails, report that failure even when a local/private draft exists.
The open PowerPoint canvas is not changed by creating a separate file.
