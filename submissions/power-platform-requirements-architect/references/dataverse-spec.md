# Specifying the data layer

The test for this section: **a builder who has never spoken to the user should be able to create the schema and get it materially right.** Column types and requirement levels are painful to change after data exists, so precision here pays back more than anywhere else in the spec.

## Contents
- [Naming](#naming)
- [Tables](#tables)
- [Columns](#columns)
- [Choices](#choices)
- [Relationships](#relationships)
- [Keys and identifiers](#keys-and-identifiers)
- [Calculated, rollup, and formula columns](#calculated-rollup-and-formula-columns)
- [Security configuration](#security-configuration)
- [Volumes, capacity, delegation](#volumes-capacity-delegation)
- [Reference data and migration](#reference-data-and-migration)
- [Non-Dataverse platforms](#non-dataverse-platforms)

---

## Naming

Decide once, apply everywhere. Builders that invent names produce a solution nobody can navigate.

- **Publisher prefix**: 2–8 lowercase characters, one per org or per team, consistent forever. If a prefix is already in use in the target environment (check in Phase 0), match it rather than introducing a second one.
- **Schema names**: `prefix_entityname`, lowercase, no spaces or umlauts. Display names carry the human-readable and localized form; schema names stay stable and ASCII.
- **Display names** in the language the users actually work in. German display names with English schema names is a perfectly good combination and often the right one.
- **Table naming**: singular display name, plural collection name (`Inspection` / `Inspections`).
- **Choice naming**: `prefix_entitystatus` for entity-specific, a clear domain name for global ones.
- **Don't** encode types in names (`txtName`, `dtDate`) — the platform already knows the type.

## Tables

For each table specify:

| Property | Why it matters |
|---|---|
| Display name, plural, schema name | Identity; referenced everywhere else |
| **Ownership**: user/team vs organization | Organization-owned removes per-row access control entirely. This cannot be changed later. Decide deliberately |
| Primary name column | Every table has one. Decide whether it's an autonumber, a natural name, or a composite — and its format string if autonumber |
| Audit enabled | Compliance requirement; also a capacity cost |
| Change tracking | Needed for dataflows, sync, and some integrations |
| Offline enabled | Needed if a mobile app must work without connectivity |
| Duplicate detection | Prevents the most common data-quality complaint |
| Notes/attachments enabled | And the expected size and count per record, for capacity |
| Volumes and retention | Drives capacity, delegation, and archival design |
| Hot query shape | The filter/sort combination users need most; tells the builder what must stay delegable and where an index matters |

Say explicitly when a table is **not** new: "extend existing `account` with two columns" is a fundamentally different work item from "create table", and Phase 0 should have told you which it is.

## Columns

Every column needs: display name, schema name, type, requirement level, and any constraint. Anything less and the builder guesses.

**Requirement levels** are a real four-value setting, not a boolean:
- `business_required` — blocked at save
- `application_required` — enforced by the form/app but not the platform
- `recommended` — nudged
- `optional`

A field that's only mandatory at submission is *not* business required — that's a `BR-` rule enforced in the flow or app, and saying so prevents a builder from blocking drafts.

**Type choices that bite if left vague:**

| Need | Use | Not |
|---|---|---|
| Money | Currency (with the currency field it implies) | Decimal, unless single-currency and you say so |
| Percentage / score | Decimal with stated precision and min/max | Integer, silently rounding |
| Yes/No | Boolean — but only if it will *never* need a third value | Boolean when "Unknown" is coming |
| A fixed set of values | Choice (with the option list) | Text, which becomes 14 spellings of "Pending" |
| Value from another table | Lookup | Text copy, which drifts immediately |
| Multi-select | Choices (multi-select) — check it's supported everywhere you need it | Comma-joined text |
| Long text | Multiline text with a stated max length | Single line at 100 chars, truncating |
| Date only, no time | Date Only with the behavior set (User Local / Date Only / Time-Zone Independent) | DateTime, producing off-by-one-day bugs across time zones |
| A file | File or Image column (or attachment) with size expectations | Base64 in a text field |

State max length for text, precision for decimals, min/max where a business range exists, and the **default value** where one exists. Defaults are requirements: "new inspections start as Draft" is `BR-` material and a column default at the same time.

Date/time behavior deserves an explicit call whenever the solution crosses time zones. "Due date" is almost always Date Only or Time-Zone Independent; "submitted at" is User Local.

## Choices

Give the **actual options**, in display order, with labels in the users' language. Where integration or reporting depends on stable values, give the numeric values too, and say they must not change.

Decide global vs local (table-specific): global when two or more tables share the semantics; local when it belongs to one table only. A global choice that later needs to diverge per table is an annoying refactor, so don't globalize speculatively.

Include the **transition rules** alongside the options if it's a status choice — the option list plus "who may move it from what to what" is what makes the model buildable. Transitions belong in `business_rules`, referenced from the choice.

## Relationships

For each: type (1:N / N:N), parent, child, lookup schema name, and **cascade behavior**.

Cascade is a business decision disguised as a technical setting:
- `cascade` delete — child rows are meaningless without the parent (findings without an inspection)
- `restrict` delete — parent may not be deleted while children exist (a store with inspection history)
- `remove_link` — children survive, orphaned deliberately

Also decide assign, share, reparent, and merge behavior when access is scoped — cascading assignment is usually what people want for a parent-child work hierarchy, and rarely what they want across reference data.

Prefer 1:N with a lookup over N:N unless the relationship genuinely has no attributes and no lifecycle. N:N relationships can't carry data, and the moment someone asks "when was this link created?", you need an intersect table instead. Deciding that up front avoids a migration.

## Keys and identifiers

- **Human-readable identifier**: users and emails need one. Autonumber with a stated format (`INS-{SEQNUM:5}`) is usually right. Say whether gaps are acceptable (they will happen).
- **Alternate keys**: required whenever an external system upserts. Without one, every retry creates duplicates. Name the columns and the purpose.
- **Natural keys** from source systems (store code, employee ID, ERP document number): capture them as columns even when a GUID is the primary key, because every integration and every support conversation will use them.

## Calculated, rollup, and formula columns

State which kind and give the logic in unambiguous business terms plus, where you can, the expression:

- **Calculated** — evaluated on read, simple expressions, no cross-table aggregation
- **Rollup** — aggregates related rows, but refreshes on a schedule (roughly hourly), so it is not suitable when the value must be correct immediately
- **Formula (Power Fx)** — richer expressions, evaluated on read
- **Flow- or plug-in-maintained stored value** — when the value must be immediately correct, historically stable, or used in a delegable filter

That last distinction is the one people get wrong. If a score must drive a filtered view or a trigger condition the moment a record is saved, a rollup is the wrong mechanism. Say which you mean and why.

## Security configuration

Specify per role, per table, the privilege at the narrowest scope that works: Create / Read / Write / Delete / Append / Append To / Assign / Share, each None / User / Business Unit / Parent-Child BU / Organization.

Points worth deciding explicitly:
- **Delete is rarely right** for business data. Prefer a status change plus a `BR-` rule, and say so — otherwise a builder grants delete because the persona is "the manager".
- **Append / Append To** control whether a user can relate rows; forgetting them produces confusing failures when saving children.
- **Column security profiles** for genuinely sensitive columns, with which roles may read and write.
- **Team model**: Entra group teams keep membership where identity governance already lives.
- **Business units** when access maps to org structure. Introducing them later means re-parenting every row.

## Volumes, capacity, delegation

Record initial rows, annual growth, retention, and attachment volume per table. These numbers drive three separate things: capacity cost, archival design, and whether the app's queries will hold up.

For **delegation**, name the filter and sort combinations the app needs and flag any that won't delegate on the chosen platform. A non-delegable filter over a table that will exceed the record limit is a functional defect that appears only in production — so it belongs in the spec as a constraint, with the mitigation chosen (delegable rewrite, pre-filtered view, server-side search, or a hard cap the business accepts).

## Reference data and migration

**Reference data**: which tables need seed rows, where the authoritative list lives, how many rows, and whether it's a one-time load or an ongoing sync. Seed data is a work item with a dependency, not a footnote.

**Migration**: source, volume, data quality problems already known, field mapping (including how to resolve lookups from source codes), method (dataflow, `pac`, script, manual), cutover sequence, verification, and rollback. State what happens to records mid-process at cutover — that's the question that gets forgotten and hurts.

## Non-Dataverse platforms

If the platform is SharePoint, SQL, or an existing system, the same discipline applies with different vocabulary:

- **SharePoint**: list name, internal column names (which differ from display names and are painful once created with spaces), column types, indexed columns, view thresholds, versioning, item-level permissions, unique constraints, and the fact that there are no real relationships or cascade behavior — state how referential integrity will be maintained instead.
- **SQL**: schema, tables, columns with SQL types, keys, constraints, indexes, views for the app to read, stored procedures if used, and who owns DDL changes.
- **Existing system of record**: the read and write contracts, the fields available, and what the Power Platform side may and may not change.

The point of the section doesn't change: remove every guess a builder would otherwise have to make.
