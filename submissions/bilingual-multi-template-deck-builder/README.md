# Bilingual Multi-Template Deck Builder

**Created by [Ofir Gavish](https://github.com/OfirGavish).**

A self-contained Agent Skill designed for **Cowork, Microsoft Copilot-harness
agents in Copilot Studio, and Scout**. Four real NOVA WORKS PPTX templates ship
INSIDE the package: English/Hebrew, dark/light. No separate template download
or manual template attachment is needed when the runtime can access skill assets.

NOVA WORKS is a fictional demo brand. All example metrics are synthetic.

## What makes it different

Select one of four ready-to-use decks, then create a NEW editable presentation
by cloning its authored slide compositions. Keep the actual masters, layouts,
themes, branding and retained media instead of approximating their appearance.
Use supported native presentation tools when they can consume the actual
bundled PPTX, or the shared Python renderer when code execution has asset access.
Python is not a universal host requirement. Native charts and tables must remain
editable; the shared renderer gives repeated charts independent data.
Hebrew uses authored RTL layouts and native mixed Hebrew/English direction.

Eight compositions are included: cover, section, three cards, metrics, chart,
roadmap, decision table and closing. The original PowerPoint-specific
`nova-deck-designer` remains a separate skill. Both use the same renderer,
bindings and template assets, assembled automatically at build time.

## Install the complete package

Download or build `bilingual-multi-template-deck-builder.zip`; do not upload
GitHub's repository ZIP or only SKILL.md. The install ZIP has SKILL.md at its
root, with scripts, templates, references, examples, requirements and license.
For folder-based installation, use the complete unpacked
`bilingual-multi-template-deck-builder` folder.

Cowork clients with custom-skill upload can use that flow. In Copilot Studio,
use a Microsoft Copilot-harness agent's Build > Skills > Upload a skill flow,
not the older bot-framework skill integration. For Scout, use the app's
supported complete-skill import or file-backed registration.
See [host setup and delivery](https://github.com/microsoft/cat-agent-skills/blob/main/submissions/bilingual-multi-template-deck-builder/references/hosts.md) for precise prerequisites,
fallback boundaries and source documentation. UI and tenant capabilities vary.

The host must expose a supported handoff for the actual bundled PPTX and
supported binary file output. The native route does not require Python.
The direct-builder route additionally needs Python 3.10+,
`python-pptx>=1.0.2,<2`, `defusedxml>=0.7.1,<1`, `lxml>=4.9,<7`, and execution
access to the installed scripts and assets. A skill grants none of these capabilities.
Do not install packages into hosted Copilot sandboxes. No font binaries ship.
Check the current host's actual upload limits; this variant does not inherit
the PowerPoint packager's observed 2 MiB ZIP / 5 MiB expanded guards.
That is NOT a promise of unlimited size on any other host.

## First prompt

```text
Use bilingual-multi-template-deck-builder. First ask me for English or Hebrew,
then dark or light. Ask for my topic, audience and source facts.
Create a NEW six-slide editable deck using the selected bundled NOVA WORKS
template: cover, three-card agenda, three priorities, roadmap, decision table,
and closing. Use my facts only; mark proposed actions as proposals.
Use native presentation tools if they support the actual bundled template;
otherwise run the real bundled --probe and builder when their prerequisites
are available. Deliver the PPTX using the host's real file output. Name missing
capabilities instead of claiming success. Do not change an open presentation.
```

The shared renderer, assets and content contract come from the PowerPoint
variant. **Not every target-host route is verified.** An initial Studio
preview returned a real eight-slide Hebrew/dark deck; Cowork imported the
skill but could not pass skill-local assets to its execution/native tools.
Scout ran through a full-package file-backed registration, not a verified
ZIP-import UI. These scoped observations are not cross-host certification.
See [host-specific evidence boundaries](https://github.com/microsoft/cat-agent-skills/blob/main/submissions/bilingual-multi-template-deck-builder/references/hosts.md).

## Approved local developer use

In a user-approved local Python environment, from the unpacked skill folder:

```powershell
python -m pip install -r requirements.txt
python scripts\build_presentation.py --probe
```

Then choose an existing output directory OUTSIDE this skill folder and a new
filename. For example, from a parent directory containing the unpacked folder:

```powershell
python bilingual-multi-template-deck-builder\scripts\build_presentation.py --template en-light --content bilingual-multi-template-deck-builder\examples\pilot-en.json --output .\pilot.pptx
```

Example plans also cover Hebrew and all eight layouts. Review
[content-format.md](https://github.com/microsoft/cat-agent-skills/blob/main/submissions/bilingual-multi-template-deck-builder/references/content-format.md) before authoring real content.
The [source repository](https://github.com/OfirGavish/copilot-powerpoint-template-skill)
contains customization and packaging documentation.

## License and attribution

**This CAT edition is licensed under the standard MIT License.**
Copyright (c) 2026 Ofir Gavish. The complete terms are in `LICENSE.txt`.
Retain the copyright and permission notice in copies or substantial portions
of the software as required by MIT.

**Created by [Ofir Gavish](https://github.com/OfirGavish).** The visible creator
credit is provided for provenance; this MIT edition imposes no additional
README or project-page attribution condition.

This is a separately authorized CAT distribution. The original source
repository and its ordinary PowerPoint/portable ZIPs retain their existing
NOVA Skill Attribution License 1.0; approving this copy does not relicense
those original distributions. The runtime scripts and four NOVA WORKS
templates are the same; only the CAT license and accompanying notices differ.
Microsoft Office, third-party dependencies and fonts retain their own terms.
