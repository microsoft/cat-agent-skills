# Excel, CSV, and TSV

## Excel (.xlsx)

Use a spreadsheet-aware editor. Inspect cell values, rich text, alignment,
styles, merged ranges, worksheet views, comments, and supported text-bearing
chart/shape objects. Report inaccessible surfaces.

Treat these as separate settings:

- **Cell reading order:** SpreadsheetML alignment `readingOrder` is
  `0` for context-dependent direction, `1` for LTR, and `2` for RTL.
  Choose per affected cell from the intended base direction.
- **Horizontal alignment:** right, left, center, or general. Preserve
  intentional numeric and centered alignment.
- **Worksheet view:** `sheetView rightToLeft` changes the sheet's visual
  column progression. Do not toggle it just to repair mixed text in cells.

Preserve formulas, cached values as supported by the editor, number formats,
data types, named ranges, validation, links, filters, freeze panes, and
conditional formatting. Do not turn dates or numbers into strings.
Do not recalculate or reorder data as a side effect.

Cell styles and shared strings may be shared by many cells. Copy a style
before changing a single cell's direction; do not mutate unrelated cells.
Do not rewrite shared string text to fix a presentation setting.

There is no direct Word-style run-direction switch to apply indiscriminately
to SpreadsheetML rich-text runs. Use the cell's reading order and the native
renderer's bidi behavior. If a mixed cell still displays incorrectly, diagnose
it in Excel; obtain approval before introducing controls into a human-facing
string. Never insert controls into formulas, lookup keys, IDs, URLs, or
machine-consumed values.

Verify formula text, types, numeric values, links, merged cells, and unaffected
styles, then inspect affected ranges in Excel or the requested spreadsheet app.
State if chart text, shapes, comments, or rendering could not be checked.

## CSV and TSV

These formats store delimited values, not fonts, alignment, sheet view, or
reading-order metadata. A CSV cannot persist Excel cell direction settings.

- Identify encoding, delimiter, quoting, line endings, headers, and the target
  importer. Do not treat an encoding problem as a bidi problem.
- Preserve every parsed field, delimiter/quote convention, row and column
  order, formula-like string, leading zero, and embedded newline.
- Do not add direction controls to data values as a formatting workaround.
  They change keys, comparisons, imports, and downstream processing.
- Offer an accompanying `.xlsx` with cell formatting or an HTML view if
  persistent direction is needed. Obtain approval for a new output format.
  Keep the original delimited data unchanged.
- If generating a spreadsheet view, preserve formula-like CSV values as
  literal strings, not executable formulas. Do not execute imported content.

Compare parsed input/output records rather than a screenshot alone.
If the only problem is the importer's display, report that there is no
formatting repair to save in the CSV itself.

## Authoritative references

- [SpreadsheetML alignment](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.alignment)
- [SpreadsheetML reading order](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.alignment.readingorder)
- [Worksheet right-to-left view](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.sheetview.righttoleft)
- [CSV format and quoting, RFC 4180](https://www.rfc-editor.org/rfc/rfc4180)
