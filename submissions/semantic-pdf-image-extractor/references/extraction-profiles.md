# Extraction Profiles

Profiles tune inclusion and context while preserving the common manifest. Apply a profile only when it matches the request.

## Search and Retrieval

- Mode: `meaningful`
- Include all informational visual types.
- Produce concise factual descriptions and 3-10 searchable keywords.
- Preserve visible labels, figure numbers, product codes, and captions exactly.
- Prefer context crops that make each result independently understandable.

## Knowledge Agent

- Mode: `meaningful`
- Retain nearby explanatory text and page titles.
- Describe what question the visual can help answer without asserting facts not shown.
- Preserve full-page fallback and provenance for grounded answers.
- Mark visuals requiring domain interpretation `review-required`.

## Photos Only

- Mode: `photos`
- Include photographs and photographic panels in composites.
- Exclude logos, icons, rendered diagrams, screenshots, and decoration.
- Keep labels and captions in context crops rather than asset crops.

## Charts and Data Visualizations

- Mode: `charts`
- Include chart title, axes, units, legend, source, and footnotes in the context crop.
- Use `review-required` when values or labels are unreadable.
- Do not convert approximate visual readings into exact data values.

## Technical Diagrams

- Mode: `diagrams`
- Preserve legends, callout labels, connector lines, scale indicators, and orientation marks.
- Keep multi-panel relationships together unless each panel is independently meaningful.
- Use a higher render DPI for small labels.

## Media Library

- Mode: `all-visuals` or a user-defined type list.
- Retain logos and icons only when requested.
- Prioritize clean asset-only crops.
- Record exact and near-duplicate candidates for curation.

## Compliance or Evidence

- Mode: `meaningful`
- Never omit full-page images.
- Always create context crops for evidence-bearing visuals.
- Preserve document hash, page number, normalized coordinates, and crop hash.
- Mark uncertain boundaries or associations `review-required`.