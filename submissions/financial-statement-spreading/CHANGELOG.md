# Changelog

Versions follow semantic versioning: MAJOR.MINOR.PATCH. A MAJOR change alters the mapping file
format or a metric definition in a way that changes results; MINOR adds rules, checks or
supported layouts; PATCH fixes bugs without changing correct results. The version is printed
by `python scripts/finance_skill.py version` and stated at the top of SKILL.md.

## 1.0.0 - 2026-11-14

First release.

- Spreads annual and interim statements from text PDFs, scanned PDFs (OCR), XLSX and CSV into
  a standard three-statement spread, for operating companies, banks, insurers and conglomerates.
- Finds the primary statements in long annual reports, including two-page statements and
  footer titles; prefers consolidated over standalone statements.
- Reads Western, French (space-grouped) and Indian (lakh/crore) number formats; drops
  change-% columns; picks interim balance sheet columns by their date heading.
- Reconciliation checks, independent source-citation verification against the document, and a
  formula-driven Excel workbook and HTML report with page-level citations.
- Agent guidance (draft review items and HINTs) for EBIT without an operating profit line,
  debt from the borrowings note, one-off items itemised in the notes, and D&A excluding
  impairment.
