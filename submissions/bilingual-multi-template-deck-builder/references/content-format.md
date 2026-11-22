# Content JSON and template bindings

The direct builder consumes UTF-8 JSON with exactly `language` (`en` or `he`)
and `slides`. The language must match the selected template profile.
Each slide has `layout`, the profile's bound fields, and optional `notes`.

The shipped profiles expose these fields:

| Layout | Required content | Optional content, cleared when omitted |
|---|---|---|
| cover | title | subtitle, eyebrow, meta |
| section | title | subtitle, eyebrow, section_number |
| three-cards | title; exactly three cards with heading and body | notes |
| metrics | title; exactly three metrics with value and label | footnote |
| chart | title; chart object | subtitle, callout, callout_label, footnote |
| roadmap | title; exactly three steps with when, heading and body | notes |
| table | title; rows matching the native table's dimensions | footnote |
| closing | title, cta | subtitle, eyebrow |

`notes` is allowed on every slide. Source template speaker instructions are
cleared; only supplied notes are added to generated output.
Optional text fields are removed from the generated slide when omitted.
Required text must be non-empty. Unknown/unbound fields are errors.
Empty input object keys and literal dots in keys are rejected at every nesting
level, before binding paths are flattened. Errors identify the offending JSON
path; empty text values remain valid for optional fields and table cells. Write
structured objects/arrays (for example, a `cards` array), not keys such as
`"cards.0.heading"` or `"subtitle.text"`. Dotted strings in `templates.json`
remain supported binding paths; they are not literal input keys.

## Example plan

```json
{
  "language": "en",
  "slides": [
    {
      "layout": "cover",
      "title": "Knowledge\nsharing pilot",
      "subtitle": "A fictional departmental pilot"
    },
    {
      "layout": "three-cards",
      "title": "Three priorities",
      "cards": [
        {"heading": "Find", "body": "Identify the most useful knowledge."},
        {"heading": "Share", "body": "Support people who contribute."},
        {"heading": "Improve", "body": "Review feedback and adapt."}
      ]
    },
    {
      "layout": "closing",
      "title": "Agree the\nnext step.",
      "subtitle": "One department will participate.",
      "cta": "Choose one use case."
    }
  ]
}
```

Full six-slide plans are in the repository's `examples/pilot-en.json` and
`pilot-he.json`. `all-layouts-en.json` and `all-layouts-he.json` exercise all
eight compositions, including clearly labeled synthetic metrics.

## Charts

Use the native editable category chart. The payload is explicit about units:

```json
{
  "layout": "chart",
  "title": "Illustrative participation",
  "chart": {
    "categories": ["Phase 1", "Phase 2", "Phase 3"],
    "series": [{"name": "Synthetic participation", "values": [20, 40, 60]}],
    "number_format": "0\"%\""
  },
  "footnote": "Synthetic example only, not a forecast or customer result."
}
```

The format above treats `20` as a displayed `20%`; use `0%` for fractional
values such as `0.2`. Do not reuse the sample percentages as real evidence.
Chart categories retain their supplied chronological order, also in Hebrew.
Repeated chart slides have independent chart parts and embedded workbooks.
Additional series receive distinct accents from the selected template's theme,
while the first series keeps its authored style.
Multi-series legends use native bottom layout with reserved plot space and the
authored axis-text styling; they must not cover bars or use indistinguishable
legend swatches.
The supplied renderer supports category charts with a value axis, such as the
demo's column chart; unsupported chart families fail rather than being recast.

## Tables

The supplied decision-table reference contains four rows and three columns:

```json
{
  "layout": "table",
  "title": "Decisions needed",
  "rows": [
    ["Decision", "Status", "Next step"],
    ["Department", "Agreed", "One department"],
    ["Owner", "Not agreed", "Confirm owner"],
    ["Launch date", "Not agreed", "Agree later"]
  ]
}
```

The renderer preserves native row/cell geometry, fills and typography. Row and
column counts must match the bound reference table. For larger tables, split
the data across additional table slides or author a different reference.
Supply rows in semantic order; Hebrew profiles place the first column on
the right and set genuine RTL paragraphs inside cells.

## Custom bindings

`templates.json` maps a logical input field to a UNIQUE editable shape name:

```json
{
  "cover": {
    "reference_slide": 1,
    "fields": {
      "title": {
        "shape": "content.title",
        "type": "text",
        "required": true,
        "max_length": 100
      }
    }
  }
}
```

Dotted paths address arrays, e.g. `cards.0.heading`. Supported binding types
are `text`, `chart`, and `table`. A chart/table binding consumes the complete
structured value at its logical field path.

Bindings are not inferred from arbitrary artwork. When replacing templates,
inspect their slide indices, shape names and object types, then update the
profile. The replacement guide explains that process.

Character limits are content-density guards, not a proof of visual fit.
Keep text concise, split dense slides and inspect actual rendered output when
the host supports rendering. The helper does not flatten charts/tables,
redraw logos, install fonts, download assets or silently discard content.
Directional formatting preserves the supplied text exactly, including adjacent
Hebrew/Latin letters, hashtags and product prefixes. Supply desired spaces in
the plan; the renderer does not insert them automatically.

URLs in Hebrew text retain internationalized hosts, paths, queries and fragments
in native LTR runs. Surrounding quotes, unmatched closing brackets and terminal
sentence punctuation stay outside the URL. A comma or semicolon outside balanced
brackets immediately followed by RTL text is treated as a prose boundary, even
after a path, query or fragment. For ambiguous literal URL punctuation, supply
percent-encoded punctuation (for example `%2C` or `%3B`), or separate surrounding
prose with whitespace. This is a display-boundary convention, not URL validation
or normalization: every supplied character is preserved.
