# Region Proposal Format

Create `diagnostics/region-proposals.json` before running the crop command.

```json
{
  "schemaVersion": "visual-work-instruction-regions/1.0",
  "pages": [
    {
      "page": 1,
      "image": "pages/page-0001.png",
      "regions": [
        {
          "id": "step-001-evidence",
          "instructionId": "step-001",
          "kind": "instruction-evidence",
          "box": [0.08, 0.18, 0.48, 0.58],
          "output": "crops/step-001-evidence.png",
          "reason": "Contains the photo, numbered callout, and associated warning."
        }
      ]
    }
  ]
}
```

## Rules

- `page` is one-based and must match the page filename.
- `image` and `output` are relative to the output directory and use `/` separators.
- `box` is `[left, top, right, bottom]` in normalized page coordinates from 0 to 1.
- `left < right` and `top < bottom`.
- `id` and `instructionId` use lowercase letters, digits, and hyphens.
- `kind` is `instruction-evidence`, `instruction-photo`, `safety-warning`, or `overview`.
- `output` must be a unique PNG path under `crops/`.
- Keep a small amount of visual context around evidence crops.
- Do not create a region when the visual association is uncertain; retain the full page instead.