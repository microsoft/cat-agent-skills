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
array path. Nested repeating arrays are not supported.

Nested array paths are allowed:

```text
{{report.findings[].title}}
{{report.findings[].rating}}
```

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
- One repeating array per sample table row
- Split tokens contained within one paragraph or one table cell paragraph

## Deliberate limits

- No placeholder may span multiple paragraphs or table cells.
- No nested repeating arrays.
- No rich-text HTML/Markdown conversion inside a placeholder.
- No placeholders inside field instructions.
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
