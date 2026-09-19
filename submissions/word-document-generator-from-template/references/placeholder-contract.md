# Deterministic DOCX placeholder contract

`scripts/docx_template.py` fills plain-text placeholders in the main document,
tables, headers, and footers without flattening the surrounding Word runs.

## Scalar values

Use dotted JSON paths:

```text
{{document.title}}
{{sections.executive_summary}}
{{metadata.approval.owner}}
```

JSON:

```json
{
  "document": {"title": "Quarterly Operations Report"},
  "sections": {"executive_summary": "First line.\nSecond line."},
  "metadata": {"approval": {"owner": "Chief Operating Officer"}}
}
```

Strings, numbers, booleans, and `null` are accepted. Newlines become Word line
breaks. Objects and arrays cannot fill scalar placeholders.

Missing scalar paths are filled with `Not specified in approved sources` and
listed in the fill summary under `defaulted_fields`.

## Repeating table rows

Put one sample row in the Word table and append `[]` to the array path:

| Finding | Impact | Owner |
| --- | --- | --- |
| `{{findings[].finding}}` | `{{findings[].impact}}` | `{{findings[].owner}}` |

JSON:

```json
{
  "findings": [
    {"finding": "Finding A", "impact": "Low", "owner": "Team A"},
    {"finding": "Finding B", "impact": "High", "owner": "Team B"}
  ]
}
```

The sample row is cloned twice and removed. An empty or missing array removes
the sample row and retains the table header. A row may reference exactly one
outer array path per nesting level.

Nested object paths within an array are allowed:

```text
{{report.findings[].title}}
{{report.findings[].rating}}
```

## Nested repeating arrays

### Flat cross-product rows

Place a single sample row whose cells reference both an outer array and a nested
inner array.  The engine produces one output row for every combination of outer
item and inner item (outer × inner):

| Finding | Affected Host | IP |
| --- | --- | --- |
| `{{findings[].finding}}` | `{{findings[].hosts[].name}}` | `{{findings[].hosts[].ip}}` |

JSON:

```json
{
  "findings": [
    {
      "finding": "Finding A",
      "hosts": [
        {"name": "host-1", "ip": "10.0.0.1"},
        {"name": "host-2", "ip": "10.0.0.2"}
      ]
    },
    {
      "finding": "Finding B",
      "hosts": [
        {"name": "host-3", "ip": "10.0.0.3"}
      ]
    }
  ]
}
```

Output: 3 data rows (2 for Finding A + 1 for Finding B).  Outer fields such as
`{{findings[].finding}}` are repeated on every inner row.

Nesting may be arbitrarily deep: `{{a[].b[].c[].field}}` produces one row per
`a × b × c` combination.  All tokens within a flat row must share the same
outer array path, and all nested tokens at any given level must reference the
same next-level array name.

### Nested Word tables (Case A)

Place a nested `w:tbl` inside a cell of the outer repeating row.  Give the
inner table its own sample row that carries deeper tokens:

```
Outer table template row (repeats for each finding):
  | {{findings[].finding}} | [inner table]         |
                              inner template row:
                              | {{findings[].hosts[].name}} |
```

Each outer clone gets the inner table expanded independently against that outer
item's data, so inner rows are never mixed across outer items.

## Conditional blocks

Templates can conditionally include or exclude entire paragraphs, tables, and
table rows using `{{#if}}` / `{{#else}}` / `{{/if}}` and `{{#switch}}` /
`{{#case}}` / `{{/switch}}` markers.  Each marker must be the only content in
its paragraph or table row.  The engine removes false-branch content before
scalar replacement and row expansion, so placeholders inside excluded branches
are never evaluated.

### If / else

```text
{{#if employee.type == "permanent"}}
Annual salary: {{employee.annual_salary}}
Pension contribution: {{employee.pension_rate}}
{{#else}}
Hourly rate: {{employee.hourly_rate}}
Overtime multiplier: {{employee.overtime_multiplier}}
{{/if}}
```

The `{{#else}}` branch is optional.

**Condition forms:**

| Syntax | Meaning |
| --- | --- |
| `{{#if path}}` | Truthy: non-empty string, non-zero number, `true`, non-null |
| `{{#if path == "value"}}` | String equality |
| `{{#if path == 42}}` | Numeric equality |
| `{{#if path == true}}` | Boolean equality (`true` or `false`) |
| `{{#if path == null}}` | Null check |
| `{{#if path != value}}` | Negated equality (any of the above) |
| `{{#if expr1 && expr2}}` | Both expressions must be true (AND) |
| `{{#if expr1 \|\| expr2}}` | Either expression must be true (OR) |

Dotted paths such as `employee.contract.type` are supported.  A missing path
evaluates as falsy.

`&&` binds tighter than `||` (standard precedence), so
`a == "x" && b == "y" || c` means `(a == "x" && b == "y") || c`.
Operators inside quoted string values are not treated as logical operators.

### Switch / case

```text
{{#switch employee.status}}
{{#case "active"}}
Active since {{employee.start_date}}
{{#case "terminated"}}
Terminated on {{employee.end_date}}
{{/switch}}
```

The first matching `{{#case}}` value wins.  If no case matches, all branches
are removed.  Case values are compared as strings after `str()` coercion.

### Scope

Conditional blocks work at two levels:

**Body level** — the `{{#if}}` / `{{#switch}}` marker is a standalone body
paragraph.  The block can span body paragraphs, tables, and any mix of body
content.

**Table-row level** — the marker occupies its own table row (the row's only
visible text is the marker).  The block spans rows within the same table.

### JSON

```json
{
  "employee": {
    "type": "permanent",
    "annual_salary": "90000",
    "pension_rate": "5%",
    "status": "active",
    "start_date": "2022-01-01"
  }
}
```

### Inspect output

`inspect` surfaces conditional paths in a new `conditional_paths` key:

```json
{
  "conditional_paths": ["employee.status", "employee.type"],
  "scalar_placeholders": ["employee.annual_salary", "employee.start_date"]
}
```

### Deliberate limits

- A conditional marker paragraph must contain **only** the marker — no other text.
- `{{#if}}` and `{{#switch}}` blocks may not be nested inside one another.
- A block cannot straddle a table boundary (e.g., `{{#if}}` in the body and
  `{{/if}}` inside a table cell).
- `{{#case}}` values are compared as strings; type-aware numeric comparison is
  not supported.



Word may store a visible token across several runs:

```xml
<w:r><w:t>{{</w:t></w:r>
<w:r><w:t>document.title</w:t></w:r>
<w:r><w:t>}}</w:t></w:r>
```

The engine joins visible text while matching, then edits only the affected
`w:t` nodes. The replacement inherits the first token run's formatting.

## Word fields

The engine never writes to:

- `w:instrText`
- `w:fldChar`
- `w:fldSimple`

Before writing, it compares field instructions and field-character counts with
the template. If PAGE, NUMPAGES, TOC, REF, or another field changes, filling
fails and no output is written.

It is safe to put a token beside live fields:

```text
{{document.version}} | Page { PAGE } of { NUMPAGES } | {{document.status}}
```

Do not use a Word field itself as a placeholder.

## Supported scope

- `.docx` input and output
- Main body, tables, `header*.xml`, and `footer*.xml`
- Scalar plain text, numbers, booleans, `null`, and line breaks
- One outer array per sample table row; arbitrarily deep nested arrays
- Flat cross-product rows: one output row per outer × inner × … combination
- Nested Word table rows: inner template rows expanded per outer item
- Split tokens contained within one paragraph or one table cell paragraph

## Literal `{{` and `}}` in JSON values

If a replacement value itself contains `{{...}}` text (for example
`Use {{name}} in the payload`), the engine inserts a Unicode zero-width space
(U+200B) between consecutive brace characters at the point of insertion.  The
result is visually identical in Word (`{{name}}` still renders as `{{name}}`)
but is not matched by the unresolved-placeholder scanner, so fill and validate
succeed for otherwise valid content.

Template-originated tokens that were never replaced are **not** escaped and
therefore still fail the unresolved check as expected.

## Deliberate limits

- No placeholder may span multiple paragraphs or table cells.
- No rich-text HTML/Markdown conversion inside a placeholder.
- No placeholders inside field instructions.
- A flat cross-product row may not mix tokens from a direct inner array and
  tokens from a nested-table inner array in the same `w:tr`.
- Content controls and legacy MERGEFIELD values are preserved, not used as the
  template syntax.
- Text embedded in unsupported package parts is not filled.

Use Word styles, table formatting, and surrounding fixed text in the template
to achieve the desired visual design.

## Commands

```bash
# Discover exact fields before writing JSON
python scripts/docx_template.py inspect template.docx --output manifest.json

# Fill a new document
python scripts/docx_template.py fill template.docx data.json output.docx \
  --summary fill-summary.json

# Verify package integrity, unresolved tokens, and live fields
python scripts/docx_template.py validate output.docx \
  --template template.docx --output validation.json
```

All failures return exit code `2` and print a specific error. The original
template is never overwritten.
