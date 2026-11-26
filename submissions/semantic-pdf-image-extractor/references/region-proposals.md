# Region Proposal Contract

Create `diagnostics/region-proposals.json` after inspecting all rendered pages and before running `crop`.

```json
{
  "schemaVersion": "semantic-pdf-image-regions/1.0",
  "documents": [
    {
      "documentId": "annual-report",
      "pages": [
        {
          "pageNumber": 3,
          "image": "pages/annual-report/page-0003.png",
          "regions": [
            {
              "assetId": "annual-report-asset-0001",
              "occurrenceId": "annual-report-occurrence-0001",
              "assetType": "chart",
              "assetBox": [0.12, 0.18, 0.88, 0.62],
              "contextBox": [0.08, 0.11, 0.92, 0.71],
              "assetOutput": "assets/annual-report/asset-0001.png",
              "contextOutput": "context/annual-report/asset-0001-context.png",
              "reason": "Chart with a separate title, legend, and source note."
            }
          ]
        }
      ]
    }
  ]
}
```

## Coordinate Rules

- Boxes are `[left, top, right, bottom]` in normalized page coordinates.
- Every value is between 0 and 1, `left < right`, and `top < bottom`.
- The Python helper is the normative validator for coordinate ordering because JSON Schema
  2020-12 cannot compare values at different array positions.
- `assetBox` tightly encloses the coherent visual.
- `contextBox` is optional. When present, it contains `assetBox` and adds only the caption, legend, labels, callouts, or prose needed to interpret the asset.
- Use the full page instead of a misleading crop when a coherent boundary cannot be established.

## Identity and Path Rules

- IDs use lowercase letters, digits, and hyphens.
- Asset IDs are globally unique in the extraction result. Prefix them with the document ID, for example `annual-report-asset-0001`.
- Occurrence IDs are globally unique. Prefix them with the document ID, for example `annual-report-occurrence-0001`. Repeated appearances of one visual share an asset ID but have different occurrence IDs and crop paths.
- `image`, `assetOutput`, and `contextOutput` are relative paths with `/` separators.
- Asset outputs are PNG files below `assets/<document-id>/`.
- Context outputs are PNG files below `context/<document-id>/`.
- Never use raw PDF text in a filename.

## Asset Types

Use one of `photo`, `diagram`, `chart`, `map`, `screenshot`, `illustration`, `table-image`, `logo`, `icon`, `composite`, or `other`.

## Context Guidance

Create a context crop when an isolated asset would lose:

- A caption, title, legend, axis label, source note, or figure number
- An arrow, callout, or numbered relationship
- A nearby warning or qualification
- The relationship between panels in a composite

Omit it when the asset is self-contained or the context crop would be nearly identical to the full page.

## Crop Results

The crop command writes `diagnostics/crop-results.json` in proposal order. Each record has an
explicit `status`:

- `created` records contain the asset and optional context pixel boxes plus their quality objects.
- `rejected` records identify an undersized candidate by asset ID, occurrence ID, document, page,
  source page path, asset output path, pixel box, and reason. No crop file is written for that
  record.

Duplicate detection examines only `created` records and records the SHA-256 of the crop-results
input. Packaging includes duplicate suggestions only when that checksum still matches the current
`diagnostics/crop-results.json`.
