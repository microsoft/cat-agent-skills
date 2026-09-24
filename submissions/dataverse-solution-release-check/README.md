# Dataverse Solution Release Check

Checks an exported Dataverse solution `.zip` before you import or ship it. It works offline and
tells you:

- what will fail, or quietly misbehave, when the package goes into a clean environment
- which solutions the target must already have
- what someone has to do before, during and after the import

## What it checks

| Check | What it catches | Result |
|---|---|---|
| Missing dependencies | Components from your own publisher that the solution needs but doesn't contain. Components from other solutions that the target must already have. | Blocker or prerequisite |
| Table packaging | Your own tables packaged with root component behavior 1 or 2 rather than 0; fine only if the target already has the table | Warning |
| Code components on forms | A form uses one of your PCF controls, but the control isn't fully in the package (its `Controls` folder, `<CustomControls>` entry and solution component) and no other solution is named for it. A packaged control manifest that isn't valid or that the check can't read. | Blocker (a warning for such a manifest when another solution is named for the control, or when the control isn't yours and isn't used in `customizations.xml` or declared in the package) |
| PCF platform libraries | React or Fluent versions declared outside the range Microsoft allows | Blocker |
| Development builds | Control bundles built in development mode. Those contain `eval()`, which Solution checker rates Critical ([rules table](https://learn.microsoft.com/power-apps/maker/data-platform/use-powerapps-checker#best-practice-rules-used-by-solution-checker)). | Warning |
| Site map icons | An SVG in `Icon` with no `VectorIcon`. An icon that points at a web resource the package doesn't include. | Warning |
| Package integrity | Files that `customizations.xml` or a control manifest points at but the zip doesn't contain; damaged entries; a zip over the 95 MB import limit; version and publisher-prefix rules | Blocker or warning |
| Import checklist | Connection references to bind, environment variables with no value, plug-in steps, cloud flows, publishing, and importing as System Administrator when the package has plug-in assemblies | Checklist |

## Before you start

- **Runtime.** The skill runs a bundled Python script: Python 3.9 or later, standard library
  only. It works in Cowork and in Scout on Windows or macOS. It needs no network access, no
  packages and no connection to your environment.
- **Export the solution as a `.zip`.** Publish all changes first, because only published
  customizations are exported.
  - **Power Apps:** open **Solutions**, select the solution, choose **Export solution**, then
    pick **Managed** or **Unmanaged**.
  - **Power Platform CLI:** run `pac solution export --name <UniqueName> --path ./MySolution.zip`.
    Add `--managed` for a managed package.
- **Check the package you'll actually ship.** That means managed for test and production, and
  unmanaged for development environments.
- **Use the zip exactly as the export produced it.** The skill recognises and explains the
  usual wrong files: unpacked source (`pac solution unpack`) or a folder, Solution checker
  results (the SARIF file an enforcement results link downloads, a zip of SARIF reports from the
  checker API or PowerShell module, or the Excel report zip from **Download results** in Power
  Apps), and a zip of zips. A zip with duplicate entries (the same name twice, ignoring case)
  isn't checked, because the check can't tell which copy counts.
- **Give the agent the zip.**
  - **Cowork:** attach the zip with **Upload images and files**, or pick it from OneDrive or
    SharePoint with **Attach cloud files**. Cowork can't read files stored on your device, and
    attached files must be less than 200 MB.
  - **Scout:** save the zip in your Scout workspace, or give its path and approve access to
    that folder when Scout asks. Python 3.9 or later must be installed on the device.

## How to use it

Ask things like:

- "Check this solution before I import it into test."
- "Will this managed export import cleanly into a new environment?"
- "What do I have to set up after importing this?"

You get a one-line verdict, then these sections:

- blockers
- warnings
- prerequisites the target must have
- an import checklist (before, during and after the import)
- anything that couldn't be checked

Every finding shows the evidence from the zip, why it matters, the fix and a source link.
Ask for the JSON report if you want to compare two runs.

## Sample report

This is from a real run on a synthetic "Contoso" package, trimmed:

```markdown
# Solution release check: `ContosoSample` `1.0.0.0`

**Not ready: 2 blockers.** Fix them and export again before importing.

1 warning, 2 prerequisite solutions to confirm, 5 checklist items, 0 not checked. This is a
static, offline check of the zip: it can't see the target environment, so it can't promise
the import will succeed.

## Blockers

### 1. Missing component from this publisher: Web resource `contoso_form_helper.js`

- **Evidence:** solution.xml `<MissingDependencies>` lists Required Web resource
  `contoso_form_helper.js`, solution=`Active`, needed by Form `Information` on `Widget`.
- **Why it matters:** It carries this publisher's prefix (`contoso_`) and isn't in this
  package, so a clean target won't have it. Import fails when a required component is neither
  in the solution nor in the target.
- **Fix:** Add the component to this solution and export again, or install the solution that
  contains it in the target first. ...

### 2. `contoso_Contoso.StarRating` declares Fluent `9.68.0`, outside the allowed versions

- **Evidence:** `Controls/contoso_Contoso.StarRating/ControlManifest.xml` declares
  platform-library name=Fluent version=`9.68.0`. Allowed declarations (Learn, checked
  2026-09-23): 8.29.0, 8.121.1, 9.4.0 to 9.46.2. `9.68.0` is a version Learn lists as loaded
  at runtime, which is not what a manifest declares.
- ...
- **Version-sensitive:** based on Microsoft Learn as checked on 2026-09-23; re-check the source.

## Warnings

### 3. `contoso_Contoso.TagBox` looks like a development build

- **Evidence:** `Controls/contoso_Contoso.TagBox/bundle.js` (1 KiB) contains webpack's
  'The "eval" devtool has been used' banner and 1 line-leading eval( call.
- **Fix:** Rebuild the control in production mode (npm run build -- --buildMode production,
  or msbuild /p:configuration=Release for a solution project), repackage and export again.
- ...

## Prerequisites in the target environment

| Solution named in the package | Installed with | Components needed |
|---|---|---|
| `BaseCustomControlsCore (9.0.2608.4009)` | `Base Custom Controls 9.0.2608.4009` | Code component `MscrmControls.FieldControls.ToggleControl` |
| `msdynce_AppCommon (9.0.4.0066)` | `msdynce_AppCommon 9.0.26052.10001` | View `All Accounts` on `account` |

## Import checklist

### During import

- [ ] **Pick a connection for each connection reference.** ...
  - `contoso_DataverseNightly` (`Contoso Dataverse (nightly)`, connector `shared_commondataserviceforapps`)
- [ ] **Provide values for environment variables that have none.** ...
  - `contoso_ApiBaseUrl` (`API base URL`)

### After import

- [ ] **Publish all customizations.** An unmanaged import brings changes in as drafts. ...
```

## Good to know

- **It's a static check.** It reads only the zip. It can't see the target environment
  (installed solutions, existing tables, licences, data), so "no blockers" doesn't mean the
  import will succeed.
- **Some checks are version-sensitive.** The PCF platform-library ranges, the 95 MB import
  limit and the CLI rebuild advice come from Microsoft Learn, as checked on 2026-09-23. The
  VectorIcon check follows Microsoft's power-platform-skills model-apps plugin at commit
  `76eb664`, not Learn. The report marks these findings and links their sources.
- **Missing dependencies are classified from `solution.xml`.** A component counts as your own
  when `solution.xml` says `solution="Active"` or names this solution, or when its name carries
  your publisher prefix and no solution is named. Your own missing components are blockers, one
  per component however many entries list it. A prefixed component from another named
  solution, usually your own base solution, is a prerequisite marked "same publisher prefix".
  Anything else from another named solution is a prerequisite for you to confirm at the version
  listed or later, not an error. A component that is listed as missing but is also a root
  component of the package (for example a table packaged as a shell) is a warning, because the
  target may already have it.
- **Some layout details come from real exports, not Learn.** Learn documents only that
  environment variable values ship as separate JSON files in the exported zip. The layout this
  check reads is observed in real exports:
  `environmentvariabledefinitions/<schemaname>/environmentvariabledefinition.xml` with
  `environmentvariablevalues.json` beside it. If `solution.xml` lists a definition the check
  can't find a file for, it's reported under "Not checked". The report labels the other layout
  details that come from exports rather than Learn.
- **It never prints secrets.** Environment variable values, plug-in step configuration and
  connection details stay out of the report. Nothing is extracted to disk.
- **It has fixed limits.** It refuses a zip with more than 50,000 entries or whose entries
  expand to more than 1 GiB. It reads at most 64 MiB from any one file (8 MiB for flow and
  environment variable JSON) and 128 MiB in total into memory, and skips a file that expands
  more than 50 times (above 8 MiB). It parses at most 1,000,000 XML elements plus attributes
  from `solution.xml` or `customizations.xml`, 200,000 from any other XML file and 1,200,000 in
  all. Parsed XML needs about 7 times its size in memory in the exports we measured, but up to
  about 30 times for crafted XML made of tiny elements; with these caps, crafted packages
  stayed under 500 MB in our tests. The parser refuses XML with a DOCTYPE, and every entry is
  read back once (up to 256 MiB) so damaged files are reported. What a limit stops is listed
  under "Not checked", or reported as too large for the check. The exception is a code
  component's `ControlManifest.xml` that a limit for one file or the DOCTYPE rule stops: that
  is reported as `control-manifest-invalid`, because the check then can't confirm the control
  is packaged.

## How it differs from Microsoft's tools and similar skills

- **Microsoft's own tools already cover parts of this.** The Power Apps import wizard lists
  missing dependencies it detects in the target before you import. The classic export has a
  **Missing Required Components** step, and the modern export can **Run solution checker on
  export**. `pac solution create-settings --solution-zip` generates a deployment settings file
  with the zip's connection references and environment variables to fill in. What this skill
  adds: it works from the zip alone, before you have access to the target. Like the wizard's
  **Missing dependencies** page (Applications, Managed Solutions, Unmanaged Components), it
  separates your own missing components from other solutions', but without the target. It
  also checks PCF platform-library ranges, development bundles, site-map icons and files
  missing from the package. And it puts all of that into one import checklist.
- **It complements Solution checker; it doesn't replace it.** Solution checker (Power Apps
  checker) is Microsoft's online service for code quality: plug-ins, JavaScript web
  resources, flows and Power Fx. `pac solution check` uploads the zip to it. This skill checks
  packaging and import readiness offline. Run both.
- **Power Automate Documentation** documents what each cloud flow in a solution does. This
  skill reads flow JSON only to find connection references and environment variables that the
  package doesn't contain; it doesn't describe what flows do.
- **Power Automate Desktop Assessment** reviews desktop and hybrid automations for quality and
  governance. It also reads `solution.xml` and reports the number of missing dependencies,
  unmanaged packages and environment variables without a default. This skill classifies each
  missing dependency (your publisher, no installable source, or a prerequisite solution) and
  adds the PCF, site map and package-file checks and the import checklist.
