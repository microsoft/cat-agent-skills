---
name: Power BI Model Review
description: "Review a Power BI or Analysis Services semantic model (TMDL, BIM/JSON, or a pasted table/measure list) for relationship, DAX, date-handling, and naming issues, with corrected DAX for anything flagged."
agentDescription: "Use this skill whenever the user shares a Power BI or Analysis Services semantic model (a TMDL export, a BIM/JSON model definition, or a pasted list of tables, relationships, and measures) and asks for a model review, a performance check, or help fixing DAX, before writing or correcting any DAX measure for that model."
platforms: [Copilot Studio, Cowork, Scout]
tags: [power-bi, dax, semantic-model, data, review, fabric]
author: Tim Karlsson
authorUrl: "https://github.com/Timziito"
authorGithub: Timziito
version: 1.0.0
createdAt: 2026-07-26
updatedAt: 2026-07-26
---
Review the semantic model structure and DAX, report findings by category, and
propose corrected DAX where relevant.

## Instructions

1. Get the model definition. Accept a TMDL folder/export, a `.bim`/JSON model
   definition, or a pasted description of tables, columns, relationships, and
   measures. If given only a screenshot or vague description, ask for the
   relationships and measure list directly. A review needs the actual
   expressions, not a summary of them.

2. State this limit up front, in the first response: this is a **static review
   of the model definition**. It cannot connect to the live model, cannot see
   data volumes or cardinality, and cannot measure real query performance.
   Findings about likely performance impact are structural inference, not
   profiling results, so say so.

3. Check the model against each category below. Skip a category cleanly if the
   model doesn't contain what it checks (e.g. no bi-directional relationships
   to review).

4. Report findings grouped by category, worst-impact first:

   | Category | Object | Issue | Fix |
   | --- | --- | --- | --- |
   | Relationships | Sales to Customer | Bi-directional, both dimension tables | Set to single-direction; use `CROSSFILTER(..., BOTH)` inside the one measure that needs it |

   For any DAX fix, show the corrected expression in full, not a diff.

5. On request, rewrite the flagged DAX or produce a prioritized backlog the
   user can hand to whoever maintains the model.

## Review categories

**Relationships**
- Bi-directional relationships between two dimension tables, or wherever a
  single-direction relationship plus a `CROSSFILTER(..., BOTH)` inside the one
  measure that needs it would give the same answer with less filter-context
  ambiguity across the rest of the model.
- Many-to-many relationships without a documented reason.
- Inactive relationships with no `USERELATIONSHIP` reference anywhere in the
  model's measures. That's dead weight.
- Missing or inconsistent relationship cardinality (e.g. many-to-many where
  one-to-many is intended).

**Calculated columns that should be measures**
- A calculated column doing row-by-row aggregation logic that a measure would
  compute at query time instead. It costs storage and compression for no benefit.
- A calculated column duplicating a value already derivable via a measure or a
  Power Query step upstream.

**Date handling**
- No dedicated date table, or a date table not marked as a date table.
- Time-intelligence functions (`TOTALYTD`, `SAMEPERIODLASTYEAR`, etc.) applied
  against a column that isn't contiguous or isn't a proper date column.
- Role-playing date scenarios (order date vs. ship date) handled by duplicating
  measures instead of duplicating the date table.

**Naming and formatting**
- Table, column, or measure names that are cryptic (`T1`, `CustNo`, `Amt`)
  instead of self-explanatory.
- Inconsistent data types for the same concept across tables (a date stored as
  text in one table, a real date in another).
- Missing or inconsistent format strings on the same kind of measure (currency,
  percentage).
- No descriptions on key measures. Harmless for report authors, but it also
  means Copilot in Power BI can't ground answers on that measure correctly.

**Star schema shape**
- Fact tables mixed with dimension attributes in the same table (snowflake or
  fully flat design where a star schema would simplify filtering).
- Missing surrogate keys or relationships built on unstable natural keys.

**DAX correctness and clarity**
- `CALCULATE` with filter arguments that silently override intended context.
- Iterators (`SUMX`, `FILTER`) used where a plain aggregation would do.
- Division without `DIVIDE()`, risking divide-by-zero errors.
- Measures that reimplement logic another measure already provides. That's a
  correctness risk if the two drift.

## Guardrails

- Never claim to have measured performance. Frame everything as "based on the
  model definition" or "typically causes."
- Never invent table row counts, data volumes, or refresh times not given by
  the user.
- Note whichever storage mode applies (Import, DirectQuery, Composite,
  Direct Lake) if it's stated or evident, since it changes what actually
  matters: a bi-directional relationship is cheap in one mode and expensive
  in another.

## Tone

Direct, structural. State the issue, the why, and the fix. Skip the theory
lecture unless asked.
