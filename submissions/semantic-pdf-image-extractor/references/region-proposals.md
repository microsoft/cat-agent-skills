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
- `assetBox` tightly encloses the coherent visual.
- `contextBox` is optional. When present, it contains `assetBox` and adds only the caption, legend, labels, callouts, or prose needed to interpret the asset.
- Use the full page instead of a misleading crop when a coherent boundary cannot be established.

## Identity and Path Rules

- IDs use lowercase letters, digits, and hyphens.
- Asset IDs are globally unique in the extraction result.
- Occurrence IDs are globally unique. Repeated appearances of one visual share an asset ID but have different occurrence IDs and crop paths.
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