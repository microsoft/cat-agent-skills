# Brand Template Enforcer

The Brand Template Enforcer is a Microsoft Copilot Studio skill that ensures
new PowerPoint presentations and Word documents are created from approved brand
templates instead of blank files.

The skill supports:

- PowerPoint presentations and templates: `.pptx`
- Word documents and templates: `.docx` and `.dotx`

> **PowerPoint format requirement:** `.potx` template files do not work with
> this workflow. Open the `.potx` in PowerPoint and use **Save As** to create a
> `.pptx` before adding it to SharePoint or `assets/`. Renaming the extension is
> not sufficient.

The package supports templates provided through SharePoint agent knowledge or
bundled directly in the skill's `assets/` folder. The downloadable ZIP does not
include a PowerPoint or Word template, so add one through either supported route.

## Quick start

If you do not need specific written brand guidance or multi-template routing,
you do not need to edit the skill files or manifest:

1. Download `brand-template-enforcer.zip`.
2. Import it in Copilot Studio from **Build > Add skill > Upload a skill**.

The recommended approach is to make the approved PowerPoint or Word template
available through SharePoint agent knowledge. The skill automatically discovers
the compatible template and uses it when generating a file. Disabled starter
manifest entries and unresolved placeholders do not interfere with this
automatic discovery.

Bundling a template directly in the skill's `assets/` folder is also supported.
Use this option when a self-contained or offline package is more important than
central template management. You must extract the ZIP, add the template, and
repackage it before importing; the complete skill ZIP must remain within the
current 20 MB limit.

If you want more granular control, extract the ZIP and complete the applicable
placeholders:

- Fill in the brand-guidance placeholders in `SKILL.md` to specify voice, fonts,
  colors, terminology, imagery, layout, legal language, and other brand rules.
- Configure `assets/template-manifest.json` to support multiple templates,
  explicit defaults, priorities, exact SharePoint sources, and predictable
  routing by deliverable type.
- Repackage `SKILL.md`, `assets/`, and `references/` at the ZIP root before
  importing the customized skill.

## Recommended setup

**Store production templates in SharePoint and add their location as agent
knowledge.** This is the preferred approach because the brand team can update
the template in SharePoint without requiring the skill ZIP to be rebuilt and
uploaded again. At runtime, the agent resolves the configured SharePoint file
and uses the latest version available from that location.

You can bundle templates directly in `assets/` when offline portability or a
self-contained package is more important. However, Copilot Studio skills in the
new experience are currently capped at **20 MB total**, including all Markdown,
JSON, references, and template binaries.

## The manifest is optional

**The skill works without editing `assets/template-manifest.json`.** If the
agent has one clearly identifiable template for the requested format in
`assets/` or configured SharePoint knowledge, it discovers and uses that
template automatically. Disabled starter entries and unresolved manifest
placeholders are ignored; they do not block automatic discovery.

Configure the manifest when it provides a practical benefit:

| Scenario | Benefit of configuring the manifest |
| --- | --- |
| Multiple PowerPoint or Word templates | Routes executive summaries, deep dives, marketing decks, statements of work, formal letters, and other deliverables to different templates |
| A preferred fallback template | Defines an explicit default for PowerPoint or Word |
| Overlapping template purposes | Uses `priority` to determine which matching template wins |
| Users describe deliverables in different ways | Uses `useWhen` phrases such as `executive briefing`, `marketing deck`, or `formal letter` for predictable selection |
| Similar filenames or templates in several knowledge locations | Identifies the exact SharePoint URL, filename, and knowledge source |
| Image-heavy or slide-master PowerPoint templates | Stores explicit `brandRules` and enables `master-layout-only` inspection |

For a simple one-template setup, the recommended path is to leave the skill
unchanged and add the template through SharePoint agent knowledge. Alternatively,
place the template directly in `assets/` and repackage the skill. For a
multi-template setup, configure and enable one manifest entry for each template.

## Step-by-step setup

### Step 1: Extract the skill

Extract `brand-template-enforcer.zip`. Confirm that the extracted directory
contains:

```text
SKILL.md
assets/template-manifest.json
references/PPTX-GENERATION.md
references/TEMPLATE-SELECTION.md
```

Keep `SKILL.md` at the skill root.

### Step 2: Upload approved templates to SharePoint

For each PowerPoint or Word template:

1. Upload the approved `.pptx`, `.docx`, or `.dotx` file to a stable
   SharePoint location.
2. Copy the complete URL for the specific file.
3. Record the exact filename, including its extension.
4. Prefer replacing or versioning the file at the same configured location when
   the brand team publishes an update.

### Step 3: Add the template as agent knowledge in SharePoint

In Copilot Studio:

1. Open the agent.
2. Open the **Build** tab.
3. Add the SharePoint site, library, folder, or file as knowledge.
4. Record the knowledge-source name exactly as it appears in the agent.
5. Confirm that the agent identity has permission to retrieve the template.

Adding a URL to the manifest is not sufficient by itself; the SharePoint
location must also be configured as knowledge.

### Step 4: Optionally configure the template manifest

Skip this step for a simple one-template setup. Complete it when you need the
multi-template routing, defaults, priorities, exact-source mapping, or
image-template guidance described above.

Open `assets/template-manifest.json` and replace:

| Placeholder | Replace with |
| --- | --- |
| `{{POWERPOINT_TEMPLATE_SHAREPOINT_URL}}` | Complete SharePoint URL for the approved PowerPoint file |
| `{{POWERPOINT_TEMPLATE_FILE_NAME}}` | Exact PowerPoint filename, including `.pptx` |
| `{{SHAREPOINT_KNOWLEDGE_SOURCE_NAME}}` | Exact SharePoint knowledge-source name configured on the agent |

The starter manifest also contains disabled entries for common deliverables:

| Template type | URL placeholder | Filename placeholder |
| --- | --- | --- |
| Executive-summary PowerPoint | `{{EXECUTIVE_SUMMARY_PPT_SHAREPOINT_URL}}` | `{{EXECUTIVE_SUMMARY_PPT_FILE_NAME}}` |
| Deep-dive PowerPoint | `{{DEEP_DIVE_PPT_SHAREPOINT_URL}}` | `{{DEEP_DIVE_PPT_FILE_NAME}}` |
| Marketing PowerPoint | `{{MARKETING_PPT_SHAREPOINT_URL}}` | `{{MARKETING_PPT_FILE_NAME}}` |
| Statement-of-work Word document | `{{SOW_DOCX_SHAREPOINT_URL}}` | `{{SOW_DOCX_FILE_NAME}}` |
| Formal-letter Word document | `{{FORMAL_LETTER_DOCX_SHAREPOINT_URL}}` | `{{FORMAL_LETTER_DOCX_FILE_NAME}}` |

For each template you want the manifest to manage:

1. Replace its URL and filename placeholders.
2. Confirm its `knowledgeSourceName`.
3. For an image-heavy or slide-master template, complete `brandRules` and set
   `inspectionMode` to `master-layout-only`.
4. Change `enabled` from `false` to `true`.
5. Update `useWhen` with phrases users will actually say.
6. Delete unused starter entries if desired.

Then review:

- `id`: Give each template a unique lowercase, hyphenated identifier.
- `enabled`: Enable only fully configured templates.
- `defaults`: Set the default PowerPoint and Word template IDs.
- `format`: Use `powerpoint` or `word`.
- `inspectionMode`: Use `auto` normally or `master-layout-only` when OCR is not
  useful.
- `brandRules`: Declare per-template brand identity, fonts, colors, and guidance
  that cannot be extracted from image-heavy templates.
- `priority`: Higher values win when multiple templates match.
- `useWhen`: Add realistic phrases describing when the template applies.
- `sources`: List SharePoint and optional local sources in preferred order.

Add a separate manifest entry for every additional template.

### Step 5: Complete the brand guidance in `SKILL.md`

Open `SKILL.md` and search for `{{`. Replace every applicable placeholder in
the **Brand adherence guidance** section.

#### Brand identity

| Placeholder | Information needed |
| --- | --- |
| `{{BRAND_NAME}}` | Organization or brand name |
| `{{BRAND_DESCRIPTION}}` | Short description of the brand |
| `{{LOGO_USAGE_RULES}}` | Approved logo placement, sizing, and exclusions |
| `{{TRADEMARK_TEXT}}` | Required trademark or attribution language |

#### Writing style

| Placeholder | Information needed |
| --- | --- |
| `{{BRAND_VOICE_AND_TONE}}` | Approved voice, tone, and personality |
| `{{DEFAULT_AUDIENCE}}` | Default reader or presentation audience |
| `{{READING_LEVEL}}` | Target reading level |
| `{{PREFERRED_TERMS}}` | Required product, service, and organizational terminology |
| `{{PROHIBITED_TERMS}}` | Words or phrases that must not be used |
| `{{CAPITALIZATION_RULES}}` | Heading, title, and product-name capitalization |
| `{{DATE_NUMBER_CURRENCY_RULES}}` | Date, number, time, and currency conventions |
| `{{REQUIRED_LEGAL_LANGUAGE}}` | Required legal, confidentiality, or compliance text |

#### Typography

| Placeholder | Information needed |
| --- | --- |
| `{{POWERPOINT_TITLE_FONT}}` | Approved PowerPoint title font |
| `{{POWERPOINT_BODY_FONT}}` | Approved PowerPoint body font |
| `{{WORD_HEADING_FONT}}` | Approved Word heading font |
| `{{WORD_BODY_FONT}}` | Approved Word body font |
| `{{FALLBACK_FONTS}}` | Approved fonts when the primary font is unavailable |
| `{{POWERPOINT_MIN_TITLE_SIZE_PT}}` | Minimum PowerPoint title size |
| `{{POWERPOINT_MIN_BODY_SIZE_PT}}` | Minimum PowerPoint body size |
| `{{WORD_BODY_SIZE_AND_SPACING}}` | Word body size, line spacing, and paragraph spacing |

#### Color, layout, and imagery

| Placeholder | Information needed |
| --- | --- |
| `{{PRIMARY_COLOR_HEX}}` | Primary brand color |
| `{{SECONDARY_COLOR_HEX}}` | Secondary brand color |
| `{{ACCENT_COLOR_HEX}}` | Accent color |
| `{{APPROVED_BACKGROUND_COLORS}}` | Approved background palette |
| `{{APPROVED_TEXT_COLORS}}` | Approved text palette |
| `{{PROHIBITED_COLOR_COMBINATIONS}}` | Color combinations that must not be used |
| `{{MINIMUM_CONTRAST_REQUIREMENT}}` | Accessibility contrast requirement |
| `{{IMAGERY_STYLE}}` | Approved photography or illustration style |
| `{{ICON_STYLE}}` | Approved icon style |
| `{{CHART_STYLE}}` | Approved chart colors, labels, and formatting |
| `{{CONTENT_DENSITY}}` | Desired amount of content per page or slide |
| `{{MARGIN_AND_WHITESPACE_RULES}}` | Required margins, spacing, and whitespace |
| `{{FOOTER_RULES}}` | Footer, classification, confidentiality, and page-number rules |

Remove optional placeholder lines that do not apply, or replace them with
`Not specified; follow the selected template`. Do not leave raw placeholders in
a production skill.

Brand placeholders in `SKILL.md` are optional explicit guidance. Unresolved
placeholders are ignored and must never appear in generated content. Manifest
placeholders need to be replaced only for entries you enable. Placeholders shown
in disabled starter entries or `references/` can remain unchanged.

Do not rely on template inference for image-only or master-only presentations.
If text extraction returns no useful content or the master uses graphics the
runtime cannot render, declare the known fonts, colors, identity, and usage
rules in that template entry's `brandRules`.

### Step 6: Optionally bundle local templates

To use local templates instead of or in addition to SharePoint:

1. Copy the template directly into `assets/`.
2. Add an `asset` source before the SharePoint source:

```json
{
  "type": "asset",
  "path": "assets/organization-slide-master.pptx"
}
```

3. Keep the complete ZIP at or below 20 MB.
4. Rebuild and re-upload the skill whenever the local template changes.

### Step 7: Repackage and upload

Before packaging, ensure every enabled manifest entry is fully configured.
Placeholders can remain in `SKILL.md` and disabled starter entries; the skill
ignores them rather than printing them or allowing them to block template
discovery.

Create a ZIP with `SKILL.md`, `assets/`, and `references/` at the root. Upload
the ZIP from **Build > Add skill > Upload a skill** in Copilot Studio.

### Step 8: Test before production

Test at least:

1. A PowerPoint request that should use the default template.
2. A Word request if a Word template is configured.
3. A request that should select a specialized template.
4. A missing or inaccessible template.
5. A read-only request that should not invoke the skill.

Confirm that the agent retrieves the correct binary, copies it to
`/app/workspace/`, invokes `analyzing-pptx` for PowerPoint inspection, preserves
the brand, and identifies the selected template source.

## Manifest fields

### `version`

Keep this set to:

```json
"version": 1
```

### `defaults`

Specifies which template to use when no `useWhen` rule matches.

```json
"defaults": {
  "powerpoint": "executive-deck",
  "word": "standard-report"
}
```

Each value must match the `id` of an entry in `templates`.

Use `null` when there is no default:

```json
"defaults": {
  "powerpoint": null,
  "word": null
}
```

### `id`

A unique identifier for the template.

```json
"id": "executive-deck"
```

Requirements:

- Use lowercase letters, numbers, and hyphens.
- Do not use the same ID for multiple templates.
- The ID does not have to match the filename, but matching names are easier to
  maintain.

### `enabled`

Controls whether the template participates in selection:

```json
"enabled": true
```

Keep starter or incomplete entries set to `false`. Enable an entry only after
its source placeholders and selection rules are complete.

### `format`

Identifies the Office application that can use the template.

PowerPoint:

```json
"format": "powerpoint"
```

Word:

```json
"format": "word"
```

Do not use file extensions as the format value.

### `sources`

An ordered list of locations from which the actual Office template can be
retrieved.

```json
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
]
```

Requirements:

- List sources in preferred resolution order.
- For `asset`, the file must exist at the specified relative path.
- For `sharepointKnowledge`, provide the complete URL and exact filename.
- Configure the SharePoint location as knowledge on the Copilot Studio agent.
- Never enable an entry while its source contains `{{PLACEHOLDER}}` values.
- Always use forward slashes `/` for asset paths.
- Do not use local absolute paths such as `C:\Templates\template.pptx`.

### `priority`

Controls which template wins when multiple `useWhen` rules match.

```json
"priority": 100
```

Higher numbers have higher priority. A practical convention is:

| Priority | Recommended use |
| --- | --- |
| `100` | Specialized template that should win when matched |
| `50` | General-purpose template |
| `10` | Fallback template |

If two matching templates have the same priority, the agent asks the user to
choose.

### `useWhen`

Lists natural-language situations in which the template should be selected.

```json
"useWhen": [
  "executive presentation",
  "leadership review",
  "steering committee"
]
```

Use terms that users are likely to include in requests. Describe the
deliverable, audience, or scenario rather than broad words such as
`document` or `presentation`.

Good rules:

- `executive steering committee presentation`
- `customer proposal`
- `internal project status report`
- `sales pitch deck`
- `formal business letter`

Avoid overlapping rules unless priority clearly determines which template
should win.

## How template selection works

The skill selects templates in this order:

1. A template explicitly requested by the user.
2. Ignore entries where `enabled` is `false`.
3. The highest-priority compatible template whose `useWhen` rule matches.
4. The compatible enabled default declared in the manifest.
5. The only compatible template discovered in `assets/` or agent knowledge.
6. The discovered template whose filename and metadata best match the request.
7. A user selection when multiple templates remain equally suitable.

After selecting a template, the skill resolves its `sources` in order:

1. Use the local `asset` when it exists.
2. Otherwise retrieve the exact binary from `sharepointKnowledge`.
3. Stop if neither source can provide the actual Office file.

If no compatible template exists, the skill stops instead of silently creating
an unbranded file. The user can explicitly approve an unbranded exception.
