# Curation result schema

The bundled script writes `curation-results.json` with these top-level fields:

- `generatedAt`: UTC timestamp.
- `inputRoot`: Scanned directory.
- `analysisMode`: Similarity methods that completed successfully.
- `warnings`: Explicit extraction or dependency warnings.
- `summary`: Counts by extraction status and candidate type.
- `documents`: One record per scanned file.
- `duplicateGroups`: Exact or normalized-text duplicate groups.
- `similarityCandidates`: Near-duplicate and related-content pairs.
- `conflictCandidates`: Similar documents containing potentially inconsistent
  directives, dates, or numeric values.
- `staleCandidates`: Documents older than the configured threshold.
- `backlog`: Prioritized human-review actions.

## Backlog fields

| Field | Meaning |
| --- | --- |
| `priority` | `Critical`, `High`, `Medium`, or `Low` |
| `category` | Duplicate, conflict, stale, extraction, or related-content review |
| `recommendedAction` | Human-review recommendation; never an automatic change |
| `primaryDocument` | Candidate document to inspect first |
| `primaryPath` | Relative location when filenames alone are ambiguous |
| `primaryPage` | One-based PDF page containing the cited excerpt |
| `primaryExcerpt` | Passage showing the conflict or duplicated content |
| `relatedDocument` | Optional comparison document |
| `relatedPath` | Relative location of the comparison document |
| `relatedPage` | One-based PDF page containing the comparison excerpt |
| `relatedExcerpt` | Comparison passage showing the evidence |
| `confidence` | Deterministic numeric score from 0 through 1 where available; otherwise blank. Never a human-validation status. |
| `reason` | Evidence supporting the recommendation |
| `sourceUrl` | Source location when supplied through the metadata manifest |
| `owner` | Content owner when supplied through the metadata manifest |

Document fields use filenames. Internal processing IDs are never included in
the workbook, JSON result, or HTML report. For formats without stable page
boundaries, page fields remain blank rather than using an invented page number.

## Excel workbook

`knowledge-corpus-curation-backlog-<YYYY-MM-DD-HHMMSSZ>.xlsx` always contains
exactly four worksheets in this order:

1. `Review Backlog`
2. `Summary`
3. `Document Inventory`
4. `Curation Settings`

`Curation Settings` records scope, freshness basis, thresholds, analysis
methods, warnings, and interpretation guidance. The workbook never labels an
agent-generated finding as `Human validated`.

The HTML report uses the matching filename
`knowledge-corpus-curation-report-<YYYY-MM-DD-HHMMSSZ>.html`. Both files use the
same UTC creation timestamp for each run.

If `openpyxl` is unavailable, the analyzer omits the workbook, records an
explicit warning in HTML and JSON, and uses the JSON `backlog` as the complete
list. The HTML truncation notice points to JSON rather than to a missing
workbook.

The `Review Backlog` worksheet always uses this column order:

`priority`, `category`, `recommendedAction`, `primaryDocument`, `primaryPath`,
`primaryPage`, `primaryExcerpt`, `relatedDocument`, `relatedPath`,
`relatedPage`, `relatedExcerpt`, `confidence`, `reason`, `sourceUrl`, `owner`.

The HTML report intentionally omits `primaryPath` and `relatedPath`. Its columns
are fixed as Priority, Category, Primary document, Primary page, Primary
excerpt, Related document, Related page, Related excerpt, Confidence,
Recommended action, and Reason. Its title contains the UTC creation date and
time, with source ZIP filenames displayed directly below it.

## Metadata manifest

Use `--metadata metadata.json` when the user uploads a SharePoint metadata export
alongside the source files. This preserves information that may be lost when
files are downloaded. The file can contain either a JSON array or an object
keyed by relative file path.

```json
[
  {
    "path": "Policies/Travel Policy.docx",
    "sourceUrl": "https://contoso.sharepoint.com/sites/policies/TravelPolicy.docx",
    "owner": "Travel Operations",
    "modifiedAt": "2026-05-15T18:30:00Z"
  }
]
```

Supported optional fields are `sourceUrl`, `owner`, `modifiedAt`, `title`, and
`contentType`.

Each document inventory record also includes:

- `detectedType`: Magika's content-based file classification when available.
- `detectedMimeType`: Detected MIME type.
- `effectiveExtension`: Extractor selected from detected content, with the
  filename extension used only as a fallback.
- `fileTypeMismatch`: `true` when detected content conflicts with the filename
  extension.
