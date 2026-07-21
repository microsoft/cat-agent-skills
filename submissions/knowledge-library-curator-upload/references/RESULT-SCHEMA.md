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
| `confidence` | Deterministic score where available |
| `reason` | Evidence supporting the recommendation |
| `sourceUrl` | Source location when supplied through the metadata manifest |
| `owner` | Content owner when supplied through the metadata manifest |

Document fields use filenames. Internal processing IDs are never included in
the workbook, JSON result, or HTML report. For formats without stable page
boundaries, page fields remain blank rather than using an invented page number.

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
