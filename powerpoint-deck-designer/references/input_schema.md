# Input schema

Top-level object:

| field   | type     | required | notes                                    |
|---------|----------|----------|------------------------------------------|
| title   | string   | no       | Metadata / logging only.                 |
| author  | string   | no       |                                          |
| date    | string   | no       | Any ISO or human-readable format.        |
| slides  | Slide[]  | yes      | Ordered list rendered 1:1.               |

## Slide

Common fields:

| field    | type   | notes                                             |
|----------|--------|---------------------------------------------------|
| layout   | string | One of the layouts in `layouts.md`.               |
| title    | string | Slide header (except `title` layout).             |
| subtitle | string | Optional sub-header.                              |
| notes    | string | Speaker notes.                                    |

Layout-specific fields:

- **title**: `title`, `subtitle`, `author`, `date`
- **section**: `title`, `subtitle`
- **content**: `bullets: string[]` OR `body: string`
- **two-column**: `columns: [{ title, bullets | body }, { title, bullets | body }]`
- **cards**: `cards: [{ title, body }, ...]`  (<= 6)
- **agenda**: `items: string[]`  (<= 8)
- **quote**: `quote`, `attribution`
- **closing**: `title`, `subtitle`, `contact`
- **chart**: `chart: { type, categories, series, stacked?, show_legend?, show_data_labels? }`
  - `type`: one of `bar`, `column`, `line`, `pie`, `donut`
  - `stacked` (bar/column only): `false` (default), `true`, or `"100"` / `"percent"` for 100% stacked
  - `categories`: list of strings (x-axis labels or pie slices)
  - `series`: list of `{ "name": string, "values": [number, ...] }` (pie/donut use only the first)
  - `show_legend` (default `true`), `show_data_labels` (default `true`)

  Column chart example:
  ```json
  {
    "layout": "chart",
    "title": "Adoption by product",
    "chart": {
      "type": "column",
      "categories": ["Power BI", "Power Apps", "Power Automate", "Copilot Studio"],
      "series": [
        { "name": "Backlog",   "values": [42, 31, 18, 5] },
        { "name": "Delivered", "values": [12,  9,  6, 1] }
      ]
    }
  }
  ```

  Stacked column chart example:
  ```json
  {
    "layout": "chart",
    "title": "Ideas per quarter",
    "chart": {
      "type": "column",
      "stacked": true,
      "categories": ["Q1", "Q2", "Q3", "Q4"],
      "series": [
        { "name": "Ideas",       "values": [12, 18, 22, 30] },
        { "name": "In progress", "values": [ 4,  8, 10, 14] },
        { "name": "Done",        "values": [ 2,  5,  7, 12] }
      ]
    }
  }
  ```

  Line chart example:
  ```json
  {
    "layout": "chart",
    "title": "Monthly active makers",
    "chart": {
      "type": "line",
      "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      "series": [
        { "name": "Finland", "values": [42, 48, 55, 63, 70, 78] },
        { "name": "Spain",   "values": [18, 22, 27, 30, 34, 39] }
      ]
    }
  }
  ```

## Validation rules
- Bullets: <= 6 per slide, <= 14 words per bullet.
- Cards: <= 6 per slide. Agenda items: <= 8.
- `two-column` requires exactly two columns.
- Chart categories: recommended <= 8 (<= 12 for line).
- Pie/donut charts only render one series.
- `stacked` is only valid on `bar` and `column`; ignored for line/pie/donut.
- Unknown layouts fall back to `content` but are flagged as errors under `--validate`.
