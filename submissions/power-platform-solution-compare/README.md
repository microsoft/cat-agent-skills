# Power Platform Solution Compare

Compare two versions of a Power Platform solution and get a clear account of what changed, what might break, and what the deployment needs. It reads every component collection in the export: content comparison for Dataverse schema, forms, views, security, processes, cloud flows, canvas apps (screens, controls, formulas, data sources, connections, read from the packaged `.msapp`), plug-in registrations, custom APIs, connection references, environment variables, templates, and Copilot Studio agents, and file-hash comparison for binaries such as plug-in assemblies, PCF bundles, connectors, reports, and app media.

## What it produces

- A summary table of added, removed, modified, and unchanged components by type.
- Attention items ranked by severity: removed columns, shortened fields, removed choice values, reduced privileges, changed flow triggers and run conditions, root components that change scope, new missing dependencies, and similar.
- A deployment checklist: connection references to satisfy, environment variables to set, assemblies to verify, flows that will switch on, customizations to publish, and whether an Upgrade (or Stage for upgrade) is needed to remove components.
- A detailed inventory per component type with the exact changed values.
- Release notes in plain language when you ask for them.

The comparison is read from the packages themselves. Nothing is inferred from solution names or assumed about what a release should contain.

## Before you start

Export both solution versions as `.zip` files (managed or unmanaged, but ideally the same type for both). Extracted export folders also work, including a zip extracted into a wrapper folder. Source unpacked with `pac solution unpack` should be repacked first with `pac solution pack`, or the agent can compare the per-component files directly.

The bundled script `scripts/solution_diff.py` needs Python 3.8 or later and nothing else: no packages, no network, no Power Platform connection. If your host cannot run Python, run the script locally and paste the Markdown report, or upload the extracted `solution.xml`, `customizations.xml`, and `Workflows/*.json` files and the agent compares them directly.

```bash
python3 scripts/solution_diff.py ContosoProjects_1_0_0_0.zip ContosoProjects_1_1_0_0.zip --md report.md --json report.json
python3 scripts/solution_diff.py old.zip new.zip --brief                              # pre-import check
python3 scripts/solution_diff.py old.zip new.zip --types "Security roles,Cloud flows"   # focused comparison (partial names such as "roles" work)
python3 scripts/solution_diff.py old.zip new.zip --max-changes 100                    # list more changed values per component (default 25)
```

The report gives package facts and warnings, a summary by component type, numbered attention items with severity, a deployment-inputs section (dependencies, connections, environment variables, binaries, activation changes, removed components), cross-references showing what in the new version still uses a removed column or a changed web resource or connection reference, and a per-type inventory with component facts. The JSON holds the same plus full change paths.

## Example prompts

> Compare these two exports of the Contoso Projects solution and tell me what changed between 1.0.0.0 and 1.1.0.0.

> I am about to import this managed solution into production over the attached current version. What could break, and what do I need to prepare first?

> Produce release notes for stakeholders from these two solution versions. Group changes by feature and leave out technical identifiers.

> Only compare the security roles and the cloud flows between these two packages.

## Good to know

- Canvas apps are compared by content: the script opens each `.msapp` and reports screens, components, and controls added, removed, or renamed, property and container-layout formulas changed with old and new text, component custom-property definitions changed, data sources and connections added or removed, and formulas that still reference a Dataverse column removed elsewhere in the solution. Images and media inside the app are compared by hash. App settings, themes, and Test Studio recordings are not compared. If an `.msapp` cannot be read, the report says so, shows no content rows, and compares the file hash only.
- Plug-in assembly DLLs and packages, PCF bundles, custom connector files, report definitions, and desktop flow definitions are compared by hash only. The report says they changed, not what changed inside. Use your source control for those internals.
- Fields that change on every export (introduced version, timestamps, managed flags) are ignored by default so the report shows real changes. Pass `--include-noise` to keep them.
- Comparing a managed export against an unmanaged one works but produces extra differences from packaging; the report warns about it. Comparing two packages with the same version number is fine and common between environments.
- Severity flags come from heuristics in the script. They point at what to check first; they are not an organizational risk rating.
- The packages cannot show target environment state: existing data, other solutions' layers, connections, or users. The report names these as items to verify rather than guessing.
- Large solutions with hundreds of components produce long reports. Ask for a focused comparison (`--types`) or a pre-import check (`--brief`) to keep the output short. The script holds both packages in memory. In measurements, peak use was roughly twenty times the size of customizations.xml and a solution with about 14,000 components compared in a few seconds; very large exports can need several gigabytes.
- A patch solution (`<name>_Patch_<hex>`) compared against its base reports only the components it carries; absent components are not reported as removed, because a patch does not remove anything.
- The script runs locally and sends nothing anywhere, but the report it writes can contain packaged environment variable values, connector names, flow parameters, and formula text. Review the report before pasting it into a shared chat or attaching it to a ticket.
- Source unpacked with `pac solution unpack` is refused with a message, because its split files would compare as an empty solution. Repack it first.

## Compatibility and attribution

This skill is published for Copilot Studio. It consists of Markdown instructions plus one standard-library Python script. It reads the solution package formats documented publicly by Microsoft and relies on no Microsoft tooling at runtime. It is a community contribution, not a Microsoft product, and does not replace solution checker, environment comparison tooling, or your organization's release process.
