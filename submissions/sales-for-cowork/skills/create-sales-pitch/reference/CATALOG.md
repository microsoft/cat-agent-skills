# Sales reference catalog

Choose references by narrative purpose and evidence relationship, not by chapter
or reuse quota. The package has two explicit subtrees:

- `infographic/` — editable PowerPoint donor components with native shapes,
  charts, tables, and relationship-preserving adaptation contracts.
- `icon/` — curated reusable SVG icons with a semantic machine manifest,
  category indexes, provenance, and licensing.

Read this catalog and the icon catalog completely, then only selected family
contracts, complete manifest entries, and actual assets. Finish truncated
returns before authoring, including entries and SVGs for icons retained inside
donors. Return selected SVGs through their closing tag, not just a license header;
copying resources or running a converter is not an in-context read. Sample content is
not subject-company evidence. Full-page compositions live in
`../design/patterns.md`, not in these references.

## Infographic hierarchy

`infographic/manifest.json` binds stable IDs, native types, packaged relative
paths, placeholder-data status, and integrity hashes. Each family README states
its narrative uses and protected design language.
Select an infographic whose relationship fits the evidence, not just a familiar
name. Inspect its actual native shapes, linked resources and labels before
importing a working copy. A fresh generic diagram is not packaged donor use.

### Core starting set

| ID | Narrative use / relationship | Asset |
|---|---|---|
| before-after.paired-state-rows | Problem/solution or current/future state for the same concerns | `infographic/before-after/paired-state-rows.pptx` |
| timeline.icon-phases | Company history or ordered milestones, not elapsed-time scale | `infographic/timeline/icon-phases.pptx` |
| comparison.criteria-matrix | Case proof or fair alternatives under shared criteria | `infographic/comparison/criteria-matrix.pptx` |
| allocation.partition-ring | Market/audience composition as an exhaustive additive partition | `infographic/allocation/partition-ring.pptx` |
| process.three-stations | Product workflow or operating flow with input/action/output | `infographic/process/three-stations.pptx` |

### Conditional families

| ID | Narrative use / condition | Asset |
|---|---|---|
| list.capability-grid | Product capabilities, use cases, or enablement talking points | `infographic/list/capability-grid.pptx` |
| metrics.kpi-dashboard | Coherent observations, attainment, and trend | `infographic/metrics/kpi-dashboard.pptx` |
| metrics.signed-variance-bridge | Complete signed reconciliation | `infographic/metrics/signed-variance-bridge.pptx` |
| cycle.arrow-loop-3 | Three recurring stages with a real return path | `infographic/cycle/arrow-loop-3.pptx` |
| cycle.arrow-loop-4 | Four recurring stages with a real return path | `infographic/cycle/arrow-loop-4.pptx` |
| cycle.arrow-loop-5 | Five recurring stages with a real return path | `infographic/cycle/arrow-loop-5.pptx` |
| cycle.arrow-loop-6 | Six recurring stages with a real return path | `infographic/cycle/arrow-loop-6.pptx` |
| venn.two-set-overlap | Supported intersection between two sets | `infographic/venn/two-set-overlap.pptx` |
| funnel.icon-stages | Actual attrition or explicitly schematic narrowing | `infographic/funnel/icon-stages.pptx` |
| gantt.workstream-rails | Supplied actual or proposed parallel time spans | `infographic/gantt/workstream-rails.pptx` |
| swot.four-quadrants | Supported strategic diagnosis, usually enablement or deep-dive | `infographic/swot/four-quadrants.pptx` |
| team.portrait-cards | Authorized people/roles with matching media | `infographic/team/portrait-cards.pptx` |

## Icon hierarchy

Read `icon/CATALOG.md` for semantic lookup and `icon/manifest.json` for exact
packaged relative paths. Use category indexes to avoid loading the full catalog.
The library intentionally packages canonical pitch-relevant assets rather than
every color/weight variant available upstream. Prefer theme-aware adaptation of
the canonical asset; add a static variant only when contrast cannot be achieved
safely at authoring time.

## Selection and visible use

For a general pitch, use at least one suitable packaged infographic and one
semantically appropriate packaged icon, subject to `../SKILL.md`'s explicit user
restrictions and evidence-fit exceptions. Do not invent numbers or force a
family merely to use it. Select by buyer question, relationship and meaning.
Consider multiple suitable components across distinct narrative relationships:
a capability grid for customer-task fit, a process for actual progression, or a
matrix for shared-criteria comparison. One imported diagram is not a target
ceiling, and variety has no quota. Unrelated channels are not sequential stages;
benefit lists are not timelines, partitions, funnels or causal growth.

Keep a private package-relative record: asset ID, packaged hash (`sha256` for
the donor, `source_sha256` for the icon), selected contract, destination slide
and component, and permitted adaptation. Preserve defining component identities
where possible and map source to working copy to final shapes/media. Record
recolor/conversion outputs and hashes as part of that mapping. On replacement,
update the asset ID and source/derived hashes together; remove obsolete inherited
provenance from picture descriptors and keep accessibility text descriptive. Do not put
provenance in visible text or speaker notes, or include host/research paths.

Verify the imported component's topology and semantic labels in the final
native shapes, and the icon's identity and actual visible placement after
recolor/conversion. Native donor imports need not retain whole-slide XML;
PNG-converted icons are valid with corroborated lineage. Names, hash metadata,
catalog mentions, unused media or off-canvas/obscured objects alone prove nothing.
Inspect the final rendering alongside the source and import/adaptation record.

## Adaptation invariants

Adapt working copies for the actual page while preserving the reference's
defining visual language.

Allowed:

- replace placeholder text and data with supported content;
- recolor shapes and icons to the active theme with verified contrast;
- add concise explanation or labels;
- reflow text independently of geometry;
- scale the complete component uniformly and reposition it for the chosen layout;
- substitute a semantically better curated icon while retaining node shape,
  connector logic, and hierarchy.

Fit the whole component, including nodes, connectors and text regions. Replace
inherited placeholder boxes that overlap; reflow labels and descriptions with
visible clearance while preserving topology and circular/icon proportions.
Use a wider content field or split distinct arguments before reducing text.
Check the final render at readable size; removing defining icons or shrinking
labels below the design floors does not solve crowding.

Not allowed:

- remove defining icons or nodes;
- turn circles into unrelated squares or generic cards;
- break continuous rails, arrows, loops, intersections, or table relationships;
- distort icons or circular geometry;
- imply quantitative scale where the source relationship is categorical;
- treat a donor's sample content as evidence.

Preserve chart relationships and workbooks; update data, caches, labels, and
geometry together. Native shapes are editable objects, not automatically Excel
Edit Data. SVG/PNG icons are not individually editable paths. Retain license and
source attribution while keeping all package references repo-relative.
