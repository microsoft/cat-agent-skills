# Template Selection Rules

Use this reference when the agent has access to more than one brand template.
The manifest is optional for a single-template setup.

## Manifest schema

`assets/template-manifest.json` uses this shape:

```json
{
  "version": 1,
  "defaults": {
    "powerpoint": "executive-deck",
    "word": "standard-report"
  },
  "templates": [
    {
      "id": "executive-deck",
      "enabled": true,
      "format": "powerpoint",
      "inspectionMode": "auto",
      "brandRules": {
        "brandName": "Example Brand",
        "titleFont": "Example Sans",
        "bodyFont": "Example Sans",
        "primaryColor": "#000000",
        "secondaryColor": "#FFFFFF",
        "accentColor": "#FF6600",
        "additionalGuidance": "Use approved template-native layouts."
      },
      "sources": [
        {
          "type": "asset",
          "path": "assets/executive-deck.pptx"
        },
        {
          "type": "sharepointKnowledge",
          "url": "{{EXECUTIVE_DECK_SHAREPOINT_URL}}",
          "fileName": "executive-deck.pptx",
          "knowledgeSourceName": "{{SHAREPOINT_KNOWLEDGE_SOURCE_NAME}}"
        }
      ],
      "priority": 100,
      "useWhen": [
        "executive presentation",
        "leadership review",
        "customer briefing"
      ]
    },
    {
      "id": "standard-report",
      "enabled": true,
      "format": "word",
      "sources": [
        {
          "type": "asset",
          "path": "assets/standard-report.dotx"
        },
        {
          "type": "sharepointKnowledge",
          "url": "{{STANDARD_REPORT_SHAREPOINT_URL}}",
          "fileName": "standard-report.dotx",
          "knowledgeSourceName": "{{WORD_SHAREPOINT_KNOWLEDGE_SOURCE_NAME}}"
        }
      ],
      "priority": 100,
      "useWhen": [
        "report",
        "proposal",
        "brief"
      ]
    }
  ]
}
```

## Field behavior

- `id`: Unique lowercase identifier used by `defaults`.
- `enabled`: Boolean. Disabled entries MUST be ignored during selection.
- `format`: MUST be `powerpoint` or `word`.
- `inspectionMode`: Optional. Use `auto` or `master-layout-only`.
- `brandRules`: Optional explicit brand identity, font, color, and usage rules.
  Recommended when those rules cannot be reliably observed from an image-heavy
  template.
- `sources`: Ordered locations from which the actual Office template can be
  retrieved.
- `sources[].type`: MUST be `asset` or `sharepointKnowledge`.
- `sources[].path`: For `asset`, a forward-slash path to an existing file inside
  `assets/`.
- `sources[].url`: For `sharepointKnowledge`, the complete SharePoint file URL.
- `sources[].fileName`: Exact SharePoint filename, including extension.
- `sources[].knowledgeSourceName`: Name of the SharePoint knowledge source
  configured on the Copilot Studio agent.
- `priority`: Integer used to break matching ties. Higher wins.
- `useWhen`: Natural-language deliverables or contexts that should select the
  template.
- `defaults.powerpoint`: Template `id` used when no PowerPoint rule matches.
- `defaults.word`: Template `id` used when no Word rule matches.

## Selection behavior

1. Ignore entries where `enabled` is `false`.
2. Ignore entries with unresolved placeholders. Disabled or incomplete starter
   entries do not block automatic template discovery.
3. Reject sources whose extension is incompatible with `format`.
4. Prefer an explicit user choice over every manifest rule.
5. Compare the requested deliverable and audience with each `useWhen` phrase.
6. If several entries match, choose the highest `priority`.
7. If the highest priority is tied, ask the user to choose.
8. If no entry matches, use the enabled format default.
9. Resolve the chosen template's `sources` in order.
10. Use an existing `asset` source first.
11. If the asset is absent, retrieve the exact binary from its
   `sharepointKnowledge` source.
12. If no source can return the binary file, stop instead of generating an
   unbranded file.

If no configured manifest entry applies, inventory compatible templates in
`assets/` and configured agent knowledge. Use the only compatible template
found. If multiple templates are available, compare their filenames and
available metadata with the requested deliverable; ask the user only when
multiple candidates remain equally suitable.

## Bundle customization

Add the approved `.pptx`, `.docx`, or `.dotx` files directly to
`assets/`, or store them in SharePoint and add that SharePoint location as agent
knowledge. A manifest update is unnecessary for one clearly identifiable
template. For multiple templates, update each entry's ordered `sources`. Keep
asset paths relative to the skill root and use forward slashes.

PowerPoint `.potx` files are not supported. Open the `.potx` file in PowerPoint
and use **Save As** to create a `.pptx`; do not merely rename the extension.
