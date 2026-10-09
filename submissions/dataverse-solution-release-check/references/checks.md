# Check reference

One section per check in `scripts/check_solution.py`. Each gives the finding ids, what the
check looks for, why it matters, the fix, the sources, and whether it is version-sensitive.
"Learn" means Microsoft Learn. Values marked version-sensitive were checked on 2026-09-23.
Details marked "in exports we've seen" come from real exports, not from Learn.

Severities: **blocker** (exit code 1: fix before import. The import fails, the package is
broken as shipped, or it is outside a documented requirement), **warning** (may fail or
misbehave depending on the target), **info**, **prerequisite** (something the target must
already have) and **checklist** (a step a person takes before, during or after the import).

## Unreadable input (exit code 2)

- **Ids:** `not-a-zip`, `file-not-found`, `folder`, `not-a-solution`, `unpacked-source`,
  `yaml-source`, `nested-folder`, `zip-in-zip`, `solution-xml-unparseable`,
  `customizations-xml-unparseable`, `solution-xml-doctype`, `customizations-xml-doctype`,
  `customizations-xml-missing`, `too-many-entries`, `duplicate-entries`, `too-large`,
  `unreadable-entry`, `internal-error`.
- **Looks for:** a zip with `solution.xml` at its root whose root element is `<ImportExportXml>`
  containing `<SolutionManifest>`, plus a `customizations.xml` whose root element is also
  `<ImportExportXml>` (either one with another root is `not-a-solution`). The manifest must also
  have what every export we've seen has (Learn doesn't document `solution.xml` element by
  element): a `UniqueName`, a `Version`, `Managed` 0 or 1, a `Publisher` with a `UniqueName`
  and `CustomizationPrefix`, and a `RootComponents` element whose components each have a
  `type` (identifiers vary: most have a `schemaName` or `id`, some only a `parentId`, and the
  classic site map, type 62, has none, so no identifier is required). A manifest that lacks any
  of them is `not-a-solution`; `Managed` 2, which unpacked solution source carries, gets pack
  advice. A
  version or prefix that is present but breaks the documented format is a warning instead
  (check 1). It recognises the usual wrong
  uploads: Solution checker results (a bare SARIF file, recognised by a `.sarif` name or SARIF's
  JSON shape, which is what a Managed Environments enforcement results link downloads; a zip
  holding `.sarif` files, which is what the checker web API and PowerShell module return; or a
  zip holding only Excel files, which is what **Download results** in Power Apps gives),
  `pac solution unpack` or SolutionPackager output (`Other/Solution.xml`), YAML source
  (`solution.yml`), a folder instead of a zip, a solution folder zipped one level down, and a
  zip of zips.
- **Parsing:** the check refuses any XML with a DOCTYPE, inside the XML parser, so the refusal
  holds in every encoding the parser detects. For `solution.xml` or `customizations.xml` that
  is `solution-xml-doctype` or `customizations-xml-doctype`: the file may be well-formed, but the
  check doesn't read it. `*-unparseable` means the XML isn't well-formed. `unreadable-entry`
  means `solution.xml` or `customizations.xml` fails its checksum, is truncated or can't be
  decompressed.
- **Duplicates:** the check looks entries up by name, compared without case, with backslashes
  read as slashes and any leading slash removed. `duplicate-entries` means two or more entries
  name the same path (up to 10 are listed). For this, names are also compared with empty and
  `.` path segments ignored, `..` applied, and trailing spaces and dots removed, so
  `./solution.xml` or `Controls/<name>//ControlManifest.xml` counts as a second copy. The
  package is ambiguous: the check can't tell which copy counts, so it checks nothing rather
  than silently reading one. This applies to any entry, not only `solution.xml` and
  `customizations.xml`. It is checked once `solution.xml` is found at the zip root, after the
  wrong-upload checks above, so Solution checker results or a zip of zips with repeated names
  are still recognised as such. None of the real exports we've seen has a duplicate name.
  Don't say what an import would do with the duplicates.
- **Size:** `too-large` means the export may be valid but is too large for this offline check:
  a file read into memory is over 64 MiB, expands more than 50 times (above 8 MiB), or would take
  the run past the 128 MiB it reads into memory in total; `solution.xml` or `customizations.xml`
  has more than 1,000,000 elements plus attributes, or all XML files together more than
  1,200,000; or the whole zip expands to more than 1 GiB. Say that, not that the file is unreadable.
- **Fix:** export the solution again and check the `.zip` the export produces.
- **Sources:** https://learn.microsoft.com/power-apps/maker/data-platform/use-powerapps-checker#review-the-solution-checker-report ;
  https://learn.microsoft.com/power-platform/alm/checker-api/overview#report-format ;
  https://learn.microsoft.com/troubleshoot/power-platform/dataverse/working-with-solutions/solution-checker-enforcement-import-issues

## 1. Package summary and identity

- **Ids:** `solution-too-large` (blocker, or warning in the band below),
  `solution-version-format`, `publisher-prefix`, `publisher-option-value-prefix` (warnings).
- **Looks for:** `<SolutionManifest>` `UniqueName`, `Version`, `Managed` (0 unmanaged, 1 managed),
  the publisher, and root components counted by type and behavior. The report also shows the
  `version` attribute on `<ImportExportXml>`. Learn's code-components ALM page calls
  `ImportExportXml`/`Version` the solution version, but in exports we've seen the solution
  version is `<SolutionManifest><Version>` and this attribute matches the source environment's
  `OrganizationVersion`.
- **Rules:** Learn gives the maximum solution file size as 95 MB (version-sensitive) without
  saying whether a megabyte is 1,000,000 or 1,048,576 bytes. Over 95 × 1,048,576 bytes is a
  blocker; between 95,000,000 and that is a warning. The version is
  major.minor.build.revision. A publisher prefix is 2 to 8 alphanumeric characters, starts with
  a letter and can't start with `mscrm`. The option value prefix is 10000 to 99999 (Learn's
  Publisher table reference).
- **Type codes:** labels come from Learn's componenttype table, in maker wording (Entity is
  Table, Attribute is Column, Attribute/Entity Image Configuration is Column/Table image
  configuration). The table isn't exhaustive. An unlisted code (for example 80, seen on
  model-driven apps) is unknown, not invalid.
- **Sources:** https://learn.microsoft.com/power-apps/maker/data-platform/import-update-export-solutions ;
  https://learn.microsoft.com/power-platform/alm/solution-api ;
  https://learn.microsoft.com/power-platform/developer/cli/reference/solution#pac-solution-init ;
  https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/publisher ;
  https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/solutioncomponent ;
  https://learn.microsoft.com/power-apps/developer/component-framework/code-components-alm#code-components-and-automated-build-pipelines

## 2. Missing dependencies

- **Ids:** `owned-missing-dependency` (blocker), `packaged-component-listed-missing` (warning),
  prerequisite groups, `platform-missing-dependency` (info).
- **Looks for:** `solution.xml` `<MissingDependencies>/<MissingDependency>`, one `<Required>` and one
  `<Dependent>` each. Attributes vary between entries (`schemaName`, `parentSchemaName`, `id`,
  `displayName`, `parentDisplayName`, dotted `id.*` keys) and `type` can be a number or a name
  such as `SettingDefinition`, so the check reads whatever identifying attributes are present.
- **Classification of each Required component:**
  - **Blocker:** `solution="Active"`, or the solution is this one, or it carries the publisher
    prefix (on `schemaName`, `parentSchemaName` or an `id.*` value) with no solution named. For
    views the prefix is often only on `parentSchemaName`. Exports list one entry per dependent,
    so entries are grouped: one blocker per missing component (type, name and parent), with
    the number of entries and the dependents in the evidence. The count in "Not ready: N
    blockers" therefore counts components.
  - **Warning instead of blocker:** the same component is a root component of this package (for
    example a table packaged with behavior 1 or 2 that lists itself as a missing dependency).
    For your own tables this is added to the `owned-table-not-behavior-0` warning (check 3);
    anything else is `packaged-component-listed-missing`. Don't say it "isn't in the package".
  - **Prerequisite:** any other named solution. Grouped by solution with the `<package>` app
    name when present. A prefixed component in another named solution is marked "same
    publisher prefix": usually your own base solution, which must be installed first. Some
    named solutions are platform or Microsoft app solutions; the checklist asks the user to
    confirm the target has each one at the version listed or later, not to install them all.
  - **Info:** the platform's `System` solution. The fix asks the user to confirm the target's
    Dataverse version is at least the source environment's.
- **Why:** export warns about missing components and lists them in `solution.xml`
  `<MissingDependencies>`. Import fails when required components are neither in the solution
  nor in the target, so an entry is not an error when the target already has the component.
  Having the solution isn't always enough: Learn says the error also occurs when apps were
  upgraded in the source environment but not in the target, tells you to update an outdated
  app and to import the same version of another managed solution that the source has, and
  advises keeping environments aligned to the same Dataverse and app versions. A component in
  a managed solution can depend only on managed components.
- **Fix:** add the component to the solution and export again, or install the app or solution
  that contains it in the target first.
- **Sources:** https://learn.microsoft.com/troubleshoot/power-platform/dataverse/working-with-solutions/missing-dependency-on-solution-import ;
  https://learn.microsoft.com/power-platform/alm/dependency-tracking-solution-components

## 3. Table packaging behavior

- **Id:** `owned-table-not-behavior-0` (warning).
- **Looks for:** a `RootComponent type="1"` with the publisher prefix and `behavior` 1 (Do not
  include subcomponents) or 2 (Include As Shell Only). The evidence says what
  `customizations.xml` carries for it (with behavior 2 it is usually only the listed columns,
  with no table definition) and whether `solution.xml` also lists the table as a missing
  dependency.
- **Why:** a table that doesn't exist in the target, or has never been imported into it, must be
  added with "Include all objects", otherwise the import fails with a missing dependency error.
  The check can't see the target, so this stays a warning: it is fine when the target already
  has the table. Learn gives the behavior labels but doesn't document how the "Include all
  objects" option is stored, so don't claim a mapping.
- **Fix:** if the target may not have the table, add it with "Include all objects" and export
  again. That choice can't be undone without removing the table and adding it again.
- **Sources:** https://learn.microsoft.com/power-platform/alm/segmented-solutions-alm ;
  https://learn.microsoft.com/troubleshoot/power-platform/dataverse/working-with-solutions/missing-dependency-on-solution-import ;
  https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/solutioncomponent

## 4. Code components on forms

- **Ids:** `form-control-not-packaged` (blocker), `control-manifest-invalid` (blocker, or
  warning as below), `control-packaging-inconsistent` (warning).
- **Looks for:** every form `<customControl name="...">` whose name has the publisher prefix
  (`<prefix>_<Namespace>.<Constructor>`). In exports we've seen, each packaged control appears
  in three places: the `Controls/<name>/` folder with its `ControlManifest.xml`, the
  `<CustomControls><CustomControl><Name>` entry and a `RootComponent type="66"`. A used control
  counts as packaged only when all three are present and its manifest passes the check below,
  or wasn't read because the run's total read or parse limit was reached (see below).
  Otherwise it is a blocker, unless `solution.xml` lists it as a type 66 missing dependency from
  another named solution: then it is only a prerequisite (a packaged manifest for it that fails
  the check is still `control-manifest-invalid`, as a warning). The title says the control
  "isn't in the package" when none of the three is present, and "isn't fully packaged" when
  some are; the evidence lists each as present or missing. A used control with the folder but
  no `<CustomControls>` entry or no type 66 root is this blocker, not
  `control-packaging-inconsistent`. Any other owned control present in only one or two of the
  three places is `control-packaging-inconsistent`, unless its manifest fails the check: then
  it is reported only as `control-manifest-invalid`, with the other two places in the evidence.
- **Manifests:** each packaged `Controls/<name>/ControlManifest.xml` is read once, before the
  form check, and reused by checks 5 and 8. It must be well-formed XML with a `<manifest>` root
  holding exactly one `<control>` element, with the attributes Learn marks as required (`namespace`,
  `constructor`, `version` and `display-name-key`), a `control-type` of `standard` or `virtual`
  if it has one, and exactly one `<resources>` element. `description-key`, `control-type` and
  `preview-image` are optional in Learn, so their absence isn't flagged. That is the shape
  Learn's manifest schema reference gives, and every exported manifest we've seen has it.
  A manifest that isn't well-formed or has another shape, or that the check refuses (a DOCTYPE,
  or over a limit for one file: 64 MiB, expanding more than 50 times above 8 MiB, or more than
  200,000 elements plus attributes), is `control-manifest-invalid`. It is a warning when
  `solution.xml` lists the control as a type 66 missing dependency from another named solution,
  or when the control isn't used anywhere in `customizations.xml`, has no `<CustomControls>`
  entry or type 66 root, and doesn't carry the publisher prefix (a stray folder). Otherwise it
  is a blocker. That control doesn't count as packaged, and checks 5 and 8 skip its manifest.
  If a used control also misses one of the three places, it is reported once, as
  `form-control-not-packaged`, with the manifest problem in the evidence. A refused manifest may
  be valid, but it is reported like an invalid one, because the check then can't confirm the
  control is packaged. A manifest that can't be read back from the zip is reported once, as
  `package-entry-damaged` (check 8). One that wasn't read because the run's total read or
  parse limit was reached first is different: the check never looked at that file, so it is
  listed under "Not checked" and the control isn't flagged. That line says when the control is
  used in `customizations.xml`, because the check then couldn't confirm it is packaged.
- **Also:** if `<CustomControls>` names a manifest file that's missing, `package-file-missing`
  (check 8) also reports it. Controls from Microsoft (`MscrmControls.*`,
  `Microsoft.PowerApps.*`) are ignored here; they surface as prerequisites. When the same
  control is also an owned type 66 missing dependency, it is reported once, as the blocker
  here. A `control-manifest-invalid` warning never absorbs that missing-dependency blocker:
  both are reported.
- **Why:** the form needs the component in the target. Learn: dependencies on code components
  from another solution are listed as type 66 missing dependencies, and that solution must be
  installed in the target first. The three-places layout is observed, not documented. Learn's
  manifest schema reference gives the manifest one `<control>` element, makes its `namespace`,
  `constructor`, `version` and `display-name-key` attributes required, and gives the control one
  `<resources>` element. Learn lists a few supported edits to the
  `customizations.xml` of an exported unmanaged solution (ribbon, site map, FormXml, saved
  queries and ISV.config); defining other components by editing it isn't supported. That is why
  a partly packaged control points to a hand-edited zip.
- **Fix:** add the code component to the solution and export again, or install its solution
  first. Don't edit the zip by hand.
- **Sources:** https://learn.microsoft.com/power-apps/developer/component-framework/code-components-alm ;
  https://learn.microsoft.com/power-apps/developer/component-framework/manifest-schema-reference/manifest ;
  https://learn.microsoft.com/power-apps/developer/component-framework/manifest-schema-reference/control ;
  https://learn.microsoft.com/power-platform/alm/dependency-tracking-solution-components ;
  https://learn.microsoft.com/power-apps/developer/data-platform/supported-customizations#unsupported-customizations ;
  https://learn.microsoft.com/power-platform/alm/when-edit-customization-file

## 5. PCF platform libraries (version-sensitive)

- **Ids:** `platform-library-version` (blocker), `platform-library-unknown`,
  `pcf-built-with-old-pac` (warnings).
- **Looks for:** `<platform-library name version>` in each packaged `ControlManifest.xml` that
  passes the manifest check in check 4.
  Allowed version range on 2026-09-23: React `16.14.0`; Fluent `8.29.0`, `8.121.1`, or `9.4.0`
  to `9.46.2`. Fluent 8 and Fluent 9 can't both be specified in one manifest. The versions
  Learn lists as loaded at runtime (React 17.0.2 in model-driven apps, Fluent 9.68.0) are
  outside the allowed range, so they aren't valid declarations. A virtual control whose
  `<built-by name="pac">` version is below 1.37 gets a rebuild warning.
- **Why:** Learn points to its supported platform libraries list for valid platform-library
  versions, and the declaration is outside that list's allowed range. Learn doesn't say what
  an import does with an out-of-range declaration, so don't claim the import fails.
- **Fix:** declare an allowed version, rebuild in production mode, repackage and export again.
  Re-check the Learn table first: the ranges change.
- **Sources:** https://learn.microsoft.com/power-apps/developer/component-framework/react-controls-platform-libraries#supported-platform-libraries-list ;
  https://learn.microsoft.com/power-apps/developer/component-framework/manifest-schema-reference/platform-library

## 6. Development builds

- **Id:** `dev-bundle-eval` (warning).
- **Looks for:** in any `.js` under `Controls/`, webpack's `The "eval" devtool has been used`
  banner or a line that starts with `eval(`. A plain count of `eval(` would also match the
  banner text, and a library can contain `eval` legitimately, so report it as "likely a
  development build", not proof. It looks at the first 10,000 `eval(` occurrences in each file.
- **Why:** webpack's development mode emits `eval()`. Solution checker reports it as
  web-avoid-eval (rule avoid-eval, severity Critical). With solution checker enforcement in Block
  mode on a Managed Environment, only critical violations block the import, and this is one.
  Learn also advises against deploying a development build: it is often too large to import and
  might slow runtime performance.
- **Fix:** `npm run build -- --buildMode production`, or `msbuild /p:configuration=Release` for a
  solution project, then repackage and export again.
- **Sources:** https://learn.microsoft.com/power-apps/developer/component-framework/issues-and-workarounds#when-running-power-apps-checker-with-the-solution-built-using-cli-tooling-in-default-configuration ;
  https://learn.microsoft.com/power-apps/maker/data-platform/use-powerapps-checker#best-practice-rules-used-by-solution-checker
  (the rules table, which rates avoid-eval Critical) ;
  https://learn.microsoft.com/power-apps/developer/component-framework/code-components-alm#building-pcfproj-code-component-projects ;
  https://learn.microsoft.com/power-apps/developer/component-framework/code-components-best-practices#power-apps-component-framework ;
  https://learn.microsoft.com/troubleshoot/power-platform/dataverse/working-with-solutions/solution-checker-enforcement-import-issues

## 7. Site map icons

- **Ids:** `sitemap-svg-icon-without-vectoricon`, `sitemap-vectoricon-not-a-path`,
  `sitemap-webresource-not-packaged` (warnings).
- **Looks for:** each `<SubArea>` in `AppModuleSiteMaps`. An `Icon` ending in `.svg` with no
  `VectorIcon`; a `VectorIcon` on a table subarea that is neither a `/...` path nor a
  `$webresource:` reference; an `Icon`, `VectorIcon` or `Url` that points at a publisher-prefixed
  web resource by plain `/WebResources/` path when that web resource isn't in the package. The
  out-of-box spacer `Icon` with no `VectorIcon` is normal and not flagged.
- **Why:** the VectorIcon guidance is from Microsoft's model-apps plugin
  (microsoft/power-platform-skills, pinned to commit `76eb664`), **not Microsoft Learn**: it
  treats `Icon` as the legacy raster slot and `VectorIcon` as the modern SVG slot, and says an
  SVG in `Icon` renders as a placeholder in the modern navigation. Learn documents only `Icon`,
  and says the Area icon applies only to the deprecated web client site map. Separately, Learn
  documents that a site map creates a published dependency on a web resource when the
  `$webresource:` directive is used. A plain `/WebResources/` path isn't covered by that, so it
  may not be listed as a missing dependency.
- **Fix:** set `VectorIcon` to the SVG web resource (keep a raster `Icon` as a fallback if you
  like); add referenced web resources to the solution or confirm the target has them.
- **Sources:** https://github.com/microsoft/power-platform-skills/blob/76eb664451b4fd8a322567ebf7baaa2f78568cee/plugins/model-apps/scripts/lib/app-spec.js (version-sensitive) ;
  https://learn.microsoft.com/power-apps/maker/model-driven-apps/create-site-map-app ;
  https://learn.microsoft.com/power-platform/alm/dependency-tracking-solution-components#site-map-sitemap

## 8. Package files

- **Ids:** `package-file-missing`, `package-entry-damaged` (blockers).
- **Looks for:** `FileName`, `JsonFileName` and `XamlFileName` paths in `customizations.xml`
  (web resources, code components, plug-in assemblies, processes and flows), and the `code`,
  `css`, `resx` and `img` paths in each packaged `ControlManifest.xml` that passes the manifest
  check in check 4 (relative to its `Controls/<name>/` folder), that aren't in the zip.
  Separately, every entry is read back once in chunks; an entry that fails its checksum, is truncated, or can't be decompressed is
  `package-entry-damaged`, reported once rather than under "Not checked". That read-back stops
  after 256 MiB and skips an entry that expands more than 50 times (above 8 MiB); entries it
  skips are listed under "Not checked" as not read back.
- **Why:** the package is incomplete or damaged as shipped, which usually means the zip was
  damaged or edited after export. Learn warns that invalid XML or incorrect component
  definitions in a hand-edited solution can prevent the import.
- **Fix:** export again rather than editing or re-zipping the export.
- **Sources:** https://learn.microsoft.com/power-platform/alm/when-edit-customization-file ;
  https://learn.microsoft.com/power-apps/maker/data-platform/export-solutions

## 9. Import checklist

Derived from what the package contains. Values are never printed.

- **Before import.** `unmanaged-target`: unmanaged solutions are for development, managed for
  every other environment, and an unmanaged import overwrites customizations to the same
  components irreversibly. `managed-target`: a managed solution can't be imported into the
  environment that holds its unmanaged original, and its changes arrive published.
  `install-prerequisites`: the prerequisite groups from check 2. Confirm the target has each
  solution at the version listed, or later. Install any that are missing and update any that
  are older before importing (check 2 gives Learn's basis). `plugin-assembly-privilege`: the
  System Customizer role has no create privilege on Plug-in Assembly by default, so import as
  System Administrator or with an equivalent grant.
- **During import.** `connection-reference-needs-connection`: from `customizations.xml`
  `<connectionreferences>` or a top-level `connectionreferences/` folder. In exports we've seen,
  connection references appear there and not as root components. Pick a connection for each,
  or supply them in a deployment settings file (`pac solution create-settings`, then
  `pac solution import --settings-file`); the import validates that the connections are owned
  by, or shared with, the connection reference owner. A `connectionreferences/` file the check
  can't read is listed in this item as a file to check by hand, and under Not checked, rather
  than left out. `env-var-without-value`: definitions with
  no default value and no current value. Learn documents only that values ship as separate JSON
  files in the exported zip. The layout the check reads is observed in real exports:
  `environmentvariabledefinitions/<schemaname>/environmentvariabledefinition.xml` with
  `environmentvariablevalues.json` beside it (it also accepts an
  `<EnvironmentVariableDefinitions>` element in `customizations.xml`). What the check can't read
  is listed in this item too, marked to check by hand, and under Not checked: a definition with
  no default whose values file can't be read (damaged, over 8 MiB, not JSON or nested too deeply;
  whether it ships a value is unknown, so it isn't reported as shipping one), a definition file
  that can't be parsed, and a type 380 root with no recognisable definition file. The import
  prompts only when neither the solution nor the target has a value. Shipping no value is what
  Microsoft advises. `enable-steps-and-flows-option`: "Enable Plugin steps and
  flows included in the solution" is on by default in the Power Apps import wizard. With
  `pac solution import` it is off unless you pass `--activate-plugins`; Pipelines in Power
  Platform activate by default. Without it, plug-in steps that arrive inactive stay inactive;
  clearing the wizard option doesn't deactivate flows.
- **After import.** `publish-after-unmanaged-import`: unmanaged imports arrive as drafts, so
  publish (`pac solution import --publish-changes`, or Publish all). `plugin-steps-inventory`:
  count, sync or async, images, tables, first step names; mention both the wizard option and
  `--activate-plugins`. `cloud-flows-present`: flows (`Category` 5) with their state at export
  (`StateCode` 0 off, 1 on, 2 suspended; status reason 3 is CompanyDLPViolation). The import
  attempts to restore each flow to its state at export; a flow that was on should turn on when
  its connection references get connections; importing an update doesn't change an existing
  flow's state. Title it "in the state you expect", and don't tell the user every flow must be
  turned on by hand: a flow that was off may be off on purpose.
- **Related findings.** `env-var-value-included` (info): a current value ships in the package;
  Microsoft advises definitions without values, and a value shipped in a managed solution can
  only be removed by an upgrade that excludes it. `flow-connection-reference-not-packaged` and
  `flow-environment-variable-not-packaged` (warnings): a flow's JSON names one that isn't in the
  package, so the target must already have it. When `solution.xml` already lists the same name
  as a missing dependency, there is no separate warning: an `owned-missing-dependency` blocker
  gets "Also used by cloud flow ..." in its evidence (unless it already names the flow), and a
  prerequisite stays a prerequisite. A flow whose JSON can't be read (over 8 MiB, not JSON,
  nested too deeply or an unexpected shape) is listed under Not checked, and so is a name in it
  that isn't text.
- **Sources:** https://learn.microsoft.com/power-platform/alm/solution-concepts-alm ;
  https://learn.microsoft.com/power-apps/maker/data-platform/import-update-export-solutions ;
  https://learn.microsoft.com/power-platform/developer/cli/reference/solution#pac-solution-import ;
  https://learn.microsoft.com/power-platform/alm/performance-recommendations ;
  https://learn.microsoft.com/power-apps/maker/data-platform/create-connection-reference ;
  https://learn.microsoft.com/power-platform/alm/conn-ref-env-variables-build-tools ;
  https://learn.microsoft.com/power-apps/maker/data-platform/environmentvariables ;
  https://learn.microsoft.com/power-automate/import-flow-solution#what-will-the-flow-state-be-after-import ;
  https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/workflow

## Not covered

- **The target environment:** installed solutions, existing tables, licences, security roles
  and data. No offline check can see them.
- **Code quality:** plug-ins, JavaScript web resources, flow logic and Power Fx. That is
  Solution checker, an online service (`pac solution check` uploads the zip to it). Only its
  JavaScript and TypeScript web-resource rules can run locally, through the npm package
  `@microsoft/eslint-plugin-power-apps`. A Solution checker pass doesn't guarantee import
  success either.
- **Unpublished changes:** only published customizations are exported, so they can't be in the zip.
- **Components in their own folders:** in exports we've seen, custom APIs, generative pages,
  duplicate rules and table search settings sit in their own top-level folders. They are counted
  in the summary but not checked.

Solution checker sources: https://learn.microsoft.com/power-apps/maker/data-platform/use-powerapps-checker ;
https://learn.microsoft.com/power-platform/developer/cli/reference/solution#pac-solution-check
