# Power BI Model Review

Paste in a semantic model (a TMDL export, a `.bim`/JSON model definition, or
just a written-out list of tables, relationships, and measures) and get a
structural review back: relationship design, calculated-column vs. measure
choices, date-table setup, naming, star-schema shape, and common DAX mistakes.
Corrected DAX is included wherever a fix applies.

## What it's for

Catching the modeling mistakes that don't show up until a report is slow or a
number is subtly wrong: bi-directional relationships between two dimension
tables, calculated columns doing a measure's job, time intelligence running
against a column that isn't really a date, `CALCULATE` filters that quietly
override the wrong thing.

## What it isn't

It cannot connect to your workspace or a live model. Everything is inferred
from the definition you provide. It doesn't measure real query time, doesn't
know your row counts, and won't tell you a report *is* slow, only what in the
model is likely to make it slow. Treat the output as a structured second
opinion, not a performance profile.

## Getting a TMDL export

Power BI Desktop's model view (or [Tabular Editor](https://tabulareditor.com/))
can serialize a model to TMDL folders, or use
[`Get-BimFile`/model.bim](https://learn.microsoft.com/analysis-services/tabular-models/tabular-model-programming-compatibility-level)
export from an existing workspace. A pasted list of tables/relationships/
measures works too if a full export isn't handy. The review is only as
thorough as what it's given.

## Reference

[Star schema guidance](https://learn.microsoft.com/power-bi/guidance/star-schema)
· [Bi-directional relationship guidance](https://learn.microsoft.com/power-bi/guidance/relationships-bidirectional-filtering)
· [Optimizing semantic models for Copilot](https://learn.microsoft.com/power-bi/create-reports/copilot-evaluate-data)

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
