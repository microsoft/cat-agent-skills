# Bilingual Multi-Template Deck Builder

**Created by [Ofir Gavish](https://github.com/OfirGavish).**

A self-contained Agent Skill for capable **Cowork sessions, Microsoft
Copilot-harness agents in Copilot Studio, and Scout**. Four actual NOVA WORKS
PPTX templates ship inside the package: English/Hebrew, dark/light.
NOVA WORKS is a fictional demo brand; all example metrics are synthetic.

## What it creates

Select a language and theme, then create a NEW editable presentation from the
selected reference deck, not a generic visual approximation. Eight authored
compositions are included: cover, section, three cards, metrics, category chart,
roadmap, decision table and closing.

Use supported native presentation tools when they can consume the real template
and edit every required object, or the shared Python renderer when code execution
has complete-bundle access. Masters, layouts, themes, branding and retained media
are preserved. Charts/workbooks and tables remain native and editable; repeated
charts have independent data. Additional series use distinct theme accents.

Hebrew uses genuine RTL paragraphs and authored right-to-left layouts. Supplied
text is preserved exactly, including mixed-script hashtags and product prefixes;
Latin names, URLs, emails and signed numbers stay internally LTR.

The PowerPoint-specific `nova-deck-designer` is a separate skill. Both editions
reuse one renderer, binding manifest and set of original templates.

## Install the complete package

Download or build `bilingual-multi-template-deck-builder.zip`. Do not upload
GitHub's repository archive, paste only SKILL.md, or install the partial authoring
overlay under `variants`. For folder installation, use the generated complete
`bilingual-multi-template-deck-builder` folder.

The install ZIP has SKILL.md at its root and keeps all supporting files. CAT's
generated download omits only the human README and catalog metadata, not its
templates, scripts, references, examples, requirements or license.

### Cowork

1. Use **Cowork > Customize > Add > Upload** when that custom-skill flow is
   exposed. Other Copilot clients may provide **Home > Agents > More agents >
   Add > Upload skill**; labels and tenant availability vary.
2. Upload the complete skill ZIP, not just SKILL.md. This is an Agent Skill,
   not an admin-center M365 plugin/app package.
3. Start a fresh task and explicitly select the intended installed copy.
   Duplicate imports may receive a suffix such as `-1`; select the correct
   version and remove obsolete test copies before a production rollout.

The runtime may need to stage the imported bundle from its host-managed
OneDrive location. The agent must discover that actual location using supported
metadata/file tools; no separately downloaded or manually attached template is
needed in the tested full-bundle workflow.

### Copilot Studio

1. Use an agent built with the **Microsoft Copilot harness** whose Build tab
   exposes **Skills > Add skill > Upload a skill**.
2. Upload the entire ZIP. This is not the older bot-framework "add a skill"
   integration, and uploading it does not provision an external execution action.
3. Verify the included files and start a fresh Preview chat after replacing
   an older version. Confirm actual execution and binary output in the configured
   runtime before publishing or sharing the agent.

### Scout

1. Use Scout's supported complete-skill folder/ZIP import when available, or its
   actual directory-based/file-backed installation path. Preserve the complete
   named folder and all relative resources; do not paste an instruction-only
   loader and treat that as installing the bundled assets.
2. Verify discovery through Scout's skill-loading interface. Do not modify hidden
   app configuration or assume any copied folder is automatically discovered.
3. Begin a fresh session. Choose an explicitly approved local-file destination
   or a provider-aware Co-create binary-output route that the current tools
   actually support.

Scout may normalize optional SKILL.md frontmatter on restart. Confirm the
instructions, full license, creator credit and bundled resources are intact.
The tested directory/local-file route does not certify a ZIP-import UI or every
Co-create provider.

## Runtime prerequisites and complete-bundle gate

Every route requires access to the actual selected template and supported binary
file delivery. Native generation does not require Python, but the host must be
able to preserve and edit every required native object.

The Python route additionally requires Python 3.10+,
`python-pptx>=1.0.2,<2`, `defusedxml>=0.7.1,<1`, `lxml>=4.9,<7`,
and code-execution access to the complete installed or faithfully staged bundle.
Keep the builder, `references/templates.json` and ALL FOUR original templates
under `assets/templates/`; retain the other references/examples when using them.
The actual probe AND every build verify all four manifest entries, even when
creating only an English or Hebrew deck. Staging only the chosen PPTX fails.

A skill grants none of these capabilities. Do not install packages into hosted
Copilot sandboxes. Approved local developer setup is described below.
No font binaries ship; Aptos, Aptos Display and Arial may be substituted.
Check the current client's upload constraints. The portable variant does not
inherit the PowerPoint packager's observed 2 MiB/5 MiB guards, which is not a
promise of unlimited size in other hosts.

## First prompt

```text
Use bilingual-multi-template-deck-builder. First ask for English or Hebrew,
then dark or light, unless I already supplied those choices. Ask for my topic,
audience and source facts.
Create a NEW six-slide editable deck from the selected bundled NOVA WORKS
template: cover, three-card agenda, three priorities, roadmap, decision table,
and closing. Use my facts only; label proposed actions clearly.
Use native presentation tools only if they support the actual template and
all required objects. Otherwise establish complete-bundle access and run the
real packaged --probe and builder when their prerequisites are available.
Deliver the actual PPTX through the host's supported file output. Report
missing capabilities instead of claiming success. Do not change an open deck.
```

For Hebrew, supply desired spacing in the original text. The renderer does not
insert spaces into mixed-script words or hashtags.

## Local developer use

From the complete unpacked skill in a user-approved local Python environment:

```powershell
python -m pip install -r requirements.txt
python scripts\build_presentation.py --probe
```

Choose an existing output directory OUTSIDE the skill and a new filename.
From a parent directory containing the complete folder:

```powershell
python bilingual-multi-template-deck-builder\scripts\build_presentation.py --template en-light --content bilingual-multi-template-deck-builder\examples\pilot-en.json --output .\pilot.pptx
```

Example plans cover six-slide stories and all eight layouts in both languages.
Read [content-format.md](https://github.com/microsoft/cat-agent-skills/blob/main/submissions/bilingual-multi-template-deck-builder/references/content-format.md) for supported structured
fields, number formats and 4x3 native table limits. Literal dots in input keys
are rejected; dotted paths belong to the binding manifest.

Read [host runtime contracts](https://github.com/microsoft/cat-agent-skills/blob/main/submissions/bilingual-multi-template-deck-builder/references/hosts.md) and the
[native workflow](https://github.com/microsoft/cat-agent-skills/blob/main/submissions/bilingual-multi-template-deck-builder/references/native-workflow.md) for runtime-specific handoff
and delivery boundaries. The [source repository](https://github.com/OfirGavish/copilot-powerpoint-template-skill)
contains build/customization guidance.

## Verification boundary

Earlier 1.1.1 live tests generated all four profiles in Cowork/Studio and
completed a separate Scout directory/local-file acceptance run. They established
working routes, not universal client, tenant, native-editing or provider support.
New builds require their own validation; prior receipts are not new host tests.
The skill must state missing capabilities and distinguish performed structural
or visual checks from unperformed ones.

Human setup guidance was checked against:

- [Microsoft Copilot skills](https://support.microsoft.com/en-us/microsoft-365-copilot/create-edit-skills-copilot)
- [Copilot Studio uploaded skills](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-add-existing)
- [CAT submission rules](https://github.com/microsoft/cat-agent-skills/blob/main/submissions/README.md)

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
