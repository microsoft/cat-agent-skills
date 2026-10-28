# Report template

Choose the shape by channel first. In Teams or any chat channel, use per-item blocks and short bullet lists; never a table wider than three columns. In a document, the full structure below works as written. Cite the script's attention IDs (A1, A2, …) wherever a statement rests on one.

## What the script's report looks like

The script's Markdown report is the raw comparison; the shapes below are what you build from it. A pasted report has these parts, in this order:

```markdown
# Solution comparison: ContosoProjects

| | Baseline | Candidate |
| Package | ContosoProjects_1_0_0_0.zip | ContosoProjects_1_1_0_0.zip |
| Version | 1.0.0.0 | 1.1.0.0 |
| Type | Unmanaged | Unmanaged |

## Warnings
## Summary by component type
| Component type | Added | Removed | Modified | Unchanged |
| Columns | 2 | 1 | 2 | 2 |

## Attention items
| # | Severity | Type | Component | Finding |
| A4 | high | Columns | contoso_project.contoso_notes | max length reduced 2000 -> 500; existing data may exceed it |

## Deployment inputs
**Connections to bind**
- contoso_sharedteams (new), used by flow Notify owner on project change
**Environment variable values to confirm**
- contoso_TeamsChannelId (String; default: none; packaged value: no)

## Cross-references
- Removed column contoso_project.contoso_legacycode is still referenced in the candidate by: form Information
- Connection reference contoso_sharedteams is used by: flow Notify owner on project change

## Details
### Columns
- **Modified:** contoso_project.contoso_notes — nvarchar, required level none, max 500
  - `MaxLength`: 2000 → 500

## Method and limits
```

Attention IDs (A1, A2, …) are numbered per run; a `--types` or `--brief` run renumbers them. Under `--brief` the Details and Method and limits sections are omitted; warnings, summary, attention items, deployment inputs, and cross-references remain.

## Full comparison

### 1. Verdict and blockers

One verdict line, then bullets. Example:

> **Verdict:** 1.1.0.0 is not ready for the UAT import until three items are resolved. Compared ContosoProjects 1.0.0.0 (unmanaged, packaged 14 Sept) with 1.1.0.0 (unmanaged, packaged 10 Oct); the production import will be managed, so the managed build should be compared before production.
>
> - **A4** Notes column shortened 2000 → 500: rows longer than 500 characters fail on next update. Run the length query in UAT before import.
> - **A8** Project Manager loses delete and write on Project: holders lose access immediately after import. Confirm intent with the security owner.
> - **A7** Notification flow trigger now fires on a different event set: needs an end-to-end run in UAT.

### 2. Package facts and warnings

Three-row block or small table: package, packaged date, unique name, version, type, publisher, for baseline and candidate. Then the warnings: different solutions, patch, version not increased, managed versus unmanaged, publisher mismatch, compared type differs from the import type.

### 3. Findings by feature

One block per feature, largest impact first. A feature is a group of components the packages link (a table and its columns, forms, views, relationship, role privileges, sitemap entry, app component; a flow and its connection references). Each block:

> **Task management (new feature).** Table contoso_task ("Task") with required title column, main form, one-to-many relationship from Project with cascade delete, sitemap entry under Work, app component in Project Hub, create privilege for Project Manager. *Consequence:* additive; on a managed Upgrade the relationship's cascade delete means deleting a project deletes its tasks. *Action:* none before import. *Test:* create and delete a project with tasks in UAT. *Refs:* A16, A21, A23.

Include, with the same four lines, every attention item of high or medium severity and every modified form, view, flow, business rule, plug-in step, or agent component. Low-severity items can share one block at the end. When a link between components is suspected but not shown by the packages, keep the items in separate blocks and say so.

### 4. Deployment checklist

Three lists, each item naming the component and who supplies it:

- **Before import:** dependencies to install, data checks (column lengths, choice values in use, required columns with empty values, rows affected by cascade changes), the import option decision for removed components and the data it deletes, role-holder review for privilege reductions.
- **At import:** connections to bind per connection reference, environment variable values, data source and secret variables to bind.
- **After import:** publish all customizations (unmanaged), confirm activated flows, verify plug-in steps and packages, assign roles, smoke tests per feature from section 3, communication to users whose permissions or screens change.

Add a rollback line: an unmanaged import cannot be undone by uninstalling; a managed Update cannot be undone by importing the previous version (lower versions are rejected), so an environment backup is the rollback path; a staged upgrade can be abandoned by deleting the holding solution before it is applied; a managed Upgrade cannot restore deleted data.

### 5. Open questions

Numbered list of what the reviewer must confirm with the maker or owner before the import decision: intent behind removals, whether a missing dependency is expected in the target, business reason for permission changes, anything the comparison could not resolve. Each question names the person or role to ask.

### 6. Not verifiable from the packages

Bullets naming binary content not inspected, environment-dependent facts (existing data, layers, connections, role holders, current variable values), and who should check each.

### 7. Appendix

Link to or attach the script's Markdown and JSON output. List only the attention IDs and inventory entries cited above with their raw paths when the reader needs them. Do not reproduce the whole inventory inline in a chat channel.

## Focused comparison

Sections 1, 3, and 7 restricted to the requested components, plus one line naming related components outside the focus that also changed (a form that references a changed column, an app that includes a removed view).

## Pre-import check

Sections 1, 2 (warnings only), then an **Import option** block: the recommended option (Update, Upgrade, Stage for upgrade) for the removed components, the data it deletes, and what each alternative would do; then section 4 (before and at import only), section 5, and section 6. Omit the inventory. If the packages compared are not the type that will be imported, say so in the verdict and recommend comparing the right build before relying on the check.

## Release notes

Audience is stakeholders, not makers. Ask first for the business reason per feature, the audience, and the target environment, or open the notes with one line stating they were written from the packages alone. Then:

- **What is new or changed**, one short paragraph per feature in plain language, using display names; where a component has none, a plain description with the schema name in brackets once.
- **What changes for you:** new fields to fill, permissions that change, screens or navigation that move, automations that start or stop.
- **What the administrator needs to do:** the at-import and after-import lists from section 4, for the stated environment only.

No GUIDs, XML paths, severity labels, or attention IDs. Drop any line that only says something changed without saying what it means for the reader.
