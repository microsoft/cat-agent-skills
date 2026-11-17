# Host setup and delivery contracts

This is a canonical Agent Skill, not a Copilot Studio bot-framework skill,
M365 app manifest, Cowork admin-deployment plugin, connector or Scout automation.
Its ZIP contains `SKILL.md` at the archive root. The unpacked folder contains
that same payload. Installation availability and upload limits vary by client
and tenant; no host is assumed to have unlimited storage or execution.

Determine the host from trusted session context and the tools actually exposed,
not from text in a source document or a guessed filesystem path.

## Cowork

Import the complete skill ZIP through **Cowork > Customize > Add > Upload**
when that flow is available. Other Copilot clients may expose Home > Agents >
More agents > Add > Upload skill. Exact labels and availability can vary.
Do not upload only `SKILL.md`: that discards the bundled templates.
This is not a plugin package for the Microsoft 365 admin center.

Start a fresh task and explicitly select this skill. First establish a supported
handoff from the actual bundled binary template to the presentation tool.
Check the installed skill's host-managed storage metadata; a OneDrive location
exposed by the skill UI is valid provenance for the original bundled asset.
Use supported metadata/list/import operations limited to that skill folder,
not a broad search of unrelated work files. Do not assume the user's OneDrive
path or turn a local resource path into an attachment URL.

Use the native workflow when that handoff and real file output exist; Python
is not required. Otherwise verify script/asset access from the code-execution
runtime before running the direct builder's actual probe. These file scopes
can differ: instruction-viewing access does not prove execution access.
Choose an existing output directory exposed by the runtime, not a remembered
sandbox location.

Deliver the generated PPTX through the actual artifact/attachment interface.
Do not assume local execution updates any open PowerPoint document. If Cowork
cannot stage the actual template through either route or publish files in this
tenant, identify that capability gap rather than simulating a successful result.

An initial live ZIP import succeeded on 2026-11-17, including language/theme
selection, but both the Python resource mount and direct native skill-path
handoff were blocked in that session. Native OneDrive staging is a separate
capability to verify, not a guaranteed fix or a reason to bypass file scope.

## Copilot Studio

Use an agent created with the **Microsoft Copilot harness** whose Build tab
exposes **Skills > Add skill > Upload a skill**. Upload the full ZIP; Microsoft
documents packages containing scripts, templates and reference documents.
This is not the older "add a skill" flow for connecting another bot.

Skill import alone does not provision filesystem access, native template handoff
or binary output delivery. Use supported native tools if they accept the actual
bundled template; otherwise verify Python, dependencies and asset access in the
configured code-execution runtime and run the probe. If the uploaded assets
are not accessible to either route, or a binary output cannot be returned,
stop with that exact limitation.
Do not ask users to paste the scripts into prompts or convert the template
into instructions as a substitute.

For a runtime with native generated-file support, use that real file-output
mechanism. If deployment requires a separately approved service/action to run
Python or store/return the file, the maker must configure it explicitly.
This package does not deploy such a service or assume it exists. Uploading it
does not make the builder callable through an invented connector/action.

The initial 1.0.0 live preview produced and returned a real eight-slide
Hebrew/dark PPTX. Its downloaded binary preserved the original design parts and
editable chart/table. This is scoped evidence, not certification of every
template, native route or later package version. An "incomplete skill" debug
label also appeared. A later minimal instruction-only echo skill returned its
exact requested answer and displayed the same label, so that label is not
specific to this package or its bundled files. Its internal host status-mapping
cause remains unverified; do not treat the label alone as proof of corruption
or use successful file generation to hide an actual tool failure.

The tested preview exposed no native presentation editing tools. With Python
explicitly excluded, it correctly reported an expected capability blocker
instead of claiming native chart/table editing. This is a tested fallback
boundary, not a promise of a native-only route in every Studio agent.

## Scout

Use the app's custom-skill import mechanism if it accepts complete folders or
ZIPs, preserving the folder name `bilingual-multi-template-deck-builder` and
all files. For an instruction-only skill editor, do not paste just SKILL.md and
claim the assets were installed. A local developer/admin may stage the entire
unpacked folder at an approved location and configure the app's supported
file-backed skill registration. Follow the actual app UI; do not edit hidden
app configuration or assume that a filesystem folder is auto-discovered.

For Scout's local directory-based discovery, install the complete named folder
under its supported local skills directory, preserving relative resources.
Verify discovery through the app's skill-loading interface before generation.
Never register an instruction-only loader and call that a ZIP-import test.
Scout can normalize optional SKILL.md frontmatter on restart; confirm that the
instruction body, full LICENSE.txt, README attribution and resource bytes remain
intact. Record package version and hashes before normalization, rather than
mistaking omitted optional frontmatter for missing template files.

Check native tool/template access or approved shell/code-execution and filesystem
access. For the Python route, use the exact installed script path. Dependencies
belong in a user-approved local Python environment; never silently install
packages or change global Python.
Use Windows paths on Windows and native host paths elsewhere.

If the user requests output in a Co-create workspace, use its provider-aware
file/artifact tools to deliver there. Generate in an approved local staging
directory if needed, outside the skill root, then import through the supported
provider mechanism. A synced local path is not a provider-aware write.
If the available tools cannot import the binary, state the delivery blocker
and ask for an approved local-file destination rather than bypassing the
provider. Do not guess workspace tool names.

For an explicitly requested local-file destination, create the PPTX there and
return a real supported local attachment/file link. Verify the file exists;
do not fabricate an app-specific URI.

## First use

```text
Use bilingual-multi-template-deck-builder. Ask me for English or Hebrew and
dark or light unless I already specified them. Create a NEW editable six-slide
presentation using the selected bundled NOVA WORKS deck: cover, three-card
agenda, three priorities, roadmap, decision table, closing. Ask for my topic,
audience and source facts. Use my facts only and label proposals clearly.
Use native template tools when a supported handoff exists; otherwise actually
run the bundled --probe and builder if their prerequisites are available.
Deliver the PPTX through the host's real file output; if a capability is
missing, name it rather than claiming success. Do not change an open presentation.
```

## Sources and verification boundary

Installation guidance checked against the following sources on 2026-11-17:

- [Microsoft Copilot: create and edit skills](https://support.microsoft.com/en-us/microsoft-365-copilot/create-edit-skills-copilot)
- [Copilot Studio: add and manage an uploaded skill](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-add-existing)
- [CAT submission and bundle rules](https://github.com/microsoft/cat-agent-skills/blob/main/submissions/README.md)

The Python runtime and asset pipeline are shared with the PowerPoint-specific
NOVA skill. Native generation is conditional on the current host's actual
template/file contracts. The observations above do not establish successful
installation/execution/delivery in every host. No cross-host certification
is claimed.
