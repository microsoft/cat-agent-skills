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

## Split Word runs

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
