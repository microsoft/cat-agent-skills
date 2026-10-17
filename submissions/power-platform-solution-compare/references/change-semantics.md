# Change semantics and deployment implications

How to classify what the comparison found. Severity is this skill's review heuristic, not a Microsoft classification. Confirm each item against the target environment before acting.

## What an import replaces and what it removes

The same finding has different consequences depending on the import. State the consequence for the import the user will perform.

| Finding | Unmanaged import | Managed Update | Managed Upgrade (or Stage for upgrade, once applied) |
| --- | --- | --- | --- |
| Component absent from the candidate (table, column, view, form, role, flow, step) | Stays in the target as an unmanaged customization, now ungoverned by the solution | Stays in the target | Deleted, with its data |
| Choice option absent from the candidate | Stays | Stays | Deleted; rows holding it are left with an invalid value |
| Content of a component present in both (form layout, view query, flow definition, business rule, plug-in step settings, role privilege set, sitemap, app components) | Replaced by the candidate's version | Replaced in the managed layer; an unmanaged layer in the target still wins | Replaced in the managed layer; an unmanaged layer in the target still wins |
| Column property (length, required level, format) | Applied | Applied in the managed layer | Applied in the managed layer |

So after an unmanaged import, a privilege removed from a role is removed, a control removed from a form is gone, and an action removed from a flow no longer runs, while a removed column or view is still there. Severity in the ladder below reflects potential impact on the strictest path (Upgrade); write the consequence next to it for the option actually chosen.

A **patch** (`<name>_Patch_<hex>`) carries only changed components; nothing absent from it is removed by any import option. An upgrade holding solution (`<name>_Upgrade`) is the staged new version awaiting apply.

## Severity ladder

| Severity | Meaning | Typical examples |
| --- | --- | --- |
| High | Can lose data, break integrations, or block the import | Removed table, column, relationship, choice value, view, form, or role; data type change; shortened text column; new missing dependency; changed flow trigger; removed plug-in step; privilege reductions |
| Medium | Changes behavior or needs preparation before or after import | New connection reference; environment variable without a value; changed default value; plug-in stage, mode, or filtering change; required level raised; flow actions removed; activation state changes; assembly version change; cascade behavior change |
| Low | Visible but unlikely to break anything | Labels, descriptions, layout, column widths, chart colors, new components with no dependents |

Breaking is about consumers: a removed column breaks every form, view, flow, plug-in, report, and integration that reads it, and the packages only show the consumers inside this solution. Say so when other solutions or external systems may depend on the component.

## Schema changes

- **Data type change** cannot be made in place, so two exports differ in a column's type only when the column was deleted and re-created in the source. Importing that onto a target where the column still exists with the old type fails with a type mismatch. The real path is a new column with a different name plus data migration.
- **Shortened text or reduced precision** succeeds on import but existing data longer than the new limit will fail validation on next update. Recommend a data length check in the target before import.
- **Required level raised** to required or system required affects every path that creates rows: forms, flows, integrations, imports. Existing rows with empty values are not fixed by import. A **new required column on an existing table** has the same effect; a required column on a **new** table does not, because no rows exist yet.
- **Choice value removed** leaves rows holding that value with an invalid state; filters, business rules, and flows that reference the value silently stop matching. Recommend a count of affected rows and a mapping plan.
- **Choice label renamed** is cosmetic unless external systems match on label text.
- **Auditing enabled on a table or column** starts writing audit history only if auditing is also enabled for the environment; it affects storage and may be a compliance requirement rather than a risk. **Change tracking** and **ownership** changes affect integrations and security respectively.
- **Relationship cascade behavior** changes alter what happens on delete, assign, share, and reparent. A change to cascade delete can remove child rows unexpectedly.
- **Table removed from the candidate** does not remove it from the target on a managed update import; see layering below.

## Security changes

- **Privilege lowered or removed** can block users immediately after import. Identify who holds the role in the target (not visible in the package) and test the affected operations.
- **Privilege raised or added** widens access; flag for review by whoever owns security.
- **Field security profile changes** affect secured columns across all apps.
- Role changes inside a managed solution are overridden by unmanaged customizations in the target; the package cannot show those.

## Automation changes

- **Cloud flow trigger changed** means the flow fires on different events or inputs. Treat as high and require an end-to-end run in a test environment.
- **Actions removed** may remove side effects others rely on. Actions added inside a condition branch only run on that branch. A **run-after condition** change (an action that ran after Succeeded now runs after Failed, Skipped, or TimedOut) and a **switch case value** change alter which path executes; treat them like action changes and test the affected path. A **definition parameter** change alters defaults every run depends on.
- **Connection reference added or changed** must be bound to a connection in the target at import, or the flow will not activate. `runtimeSource: invoker` means the flow runs with each caller's connection, which changes access behavior.
- **Activation state** in the package decides whether the flow is turned on after import when connections are satisfied. A flow moving from draft to activated starts running, and so does a new flow exported as activated; both appear under activation changes in the deployment inputs.
- **Business rules and classic workflows** compare by definition hash; a changed definition is flagged for review because the logic itself is not itemized, and its scope and activation state should be re-checked.
- **Plug-in step changes**: stage moves between pre-validation, pre-operation, and post-operation change what data the code sees and whether it can cancel the operation; mode changes between synchronous and asynchronous change timing and error behavior; filtering attribute changes alter when the step fires. A removed step silently stops validation or side effects.
- **Plug-in assembly version change** means new code. Only the version and type list are visible; ask for the code change log.
- **Custom API changes** to parameters, binding, or privileges break callers, including flows and external integrations.

## Configuration changes

- **Environment variable values** resolve by layer: a value set in the target (through the import wizard or the maker portal) is an unmanaged layer and wins; a current value packaged in the solution updates the managed layer and takes effect only where no unmanaged value exists; the default value applies only when there is no current value at all. So a changed packaged current value or default changes behavior only in targets that never had their own value set. A new variable of type String, Number, Boolean, or JSON (type codes 100000000 to 100000003) with no default and no packaged value must be supplied at import or dependent flows and apps fail at runtime. Data source (100000004) and Secret (100000005) variables are always bound in the target and normally carry no packaged value.
- **New missing dependency** in the manifest means the candidate needs another solution or component in the target first; import is blocked until it exists.
- **Root component behavior** (0 include subcomponents, 1 do not include, 2 shell only) decides how much of a table is carried; a change here can silently stop shipping subcomponents. The comparison reports a behavior change for any root component present in both manifests; confirm with the maker that the narrower scope is intended.
- **Canvas apps** carried in a solution are imported in their published form and do not normally need a separate publish; model-driven customizations in an unmanaged import need **Publish all customizations**. The comparison opens the `.msapp`: a **new data source or connection** means users need access and a connection on first run and a connection reference may need binding; a **removed data source** breaks formulas that still use it; a **removed screen** breaks navigation that targets it; **changed formulas** need the affected screens tested; a **formula referencing a removed Dataverse column** fails at runtime. An app reported as re-saved with no differences had no change in screens, controls, property and layout formulas, component definitions, groups, data sources, connections, or media; app settings beyond layout and name, themes, and test recordings are outside the comparison, so say so rather than calling the change cosmetic without qualification.
- **Web resource** script changes affect every form and command that loads the file; list the forms that reference it when possible.
- **Copilot Studio agent components** compare by the component `data`; a changed topic or tool needs a conversation test, and a changed authentication setting changes who can reach the agent.
- **Templates and generic records** (email, mail merge, article templates; records in collections the script reports as "Other") compare by content; the consequence is usually limited to the users of that template or record. Say which collection they belong to and ask the owner when the purpose is unclear.

## Managed and unmanaged packages

- **Managed import options**: **Update** replaces the solution with the new version but keeps components that are no longer in it. **Upgrade** installs the new version and deletes components absent from it, together with their data. **Stage for upgrade** installs the new version alongside the old one and defers that deletion until the user applies the upgrade, which allows data migration in between. Flag every removed component with this consequence and say which option the user needs.
- **Unmanaged import** never deletes anything and leaves the removed components in place as unmanaged customizations.
- **Layering**: unmanaged customizations and other managed solutions in the target override values from this package. A change that looks effective in the comparison may not be visible in the target. The packages cannot show this; recommend checking solution layers for the affected component.
- **Version rules**: importing a managed solution with a lower version than the one installed is rejected. The same version is accepted as an Update and applies the changes. An Upgrade or Stage for upgrade requires a higher version.
- **Comparing managed to unmanaged** exports of the same version shows packaging differences (managed flags, some default values); report them as packaging noise, not changes.

## Pre-import checklist

Produce this from the findings, naming the specific components and who supplies each item. The script's "Deployment inputs" section is the starting list.

**Before import**

1. Dependencies to install first.
2. Data checks in the target: column lengths against new maximums, rows holding removed choice values, required columns with empty values, rows affected by cascade changes.
3. The import option for removed components (Update keeps, Upgrade deletes, Stage for upgrade defers) and the data each option deletes.
4. Role holders for every privilege reduction, and the operations they perform.

**At import**

5. A connection for each new or changed connection reference.
6. Values for environment variables without a default or packaged value; bindings for data source and secret variables.

**After import**

7. Publish all customizations (unmanaged imports).
8. Confirm flows activated as intended; verify plug-in steps and packages registered.
9. Assign new or changed roles; tell users whose permissions or screens change.
10. Smoke tests per changed feature, each tied to a finding.

**Rollback.** An unmanaged import cannot be undone by uninstalling the solution. A managed Update cannot be undone by importing the previous version, because a lower version is rejected; roll back by restoring an environment backup. A staged upgrade can be abandoned by deleting the `<name>_Upgrade` holding solution before it is applied. A managed Upgrade or applied stage-for-upgrade cannot restore deleted components or data; back up before it.
