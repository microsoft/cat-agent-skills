---
name: Brand Template Enforcer
description: Ensure every generated PowerPoint deck or Word document starts from the correct bundled or SharePoint-hosted brand template.
agentDescription: "Applies bundled or SharePoint-hosted organization-approved PowerPoint and Word templates whenever the agent is about to create, generate, export, or substantially rebuild a presentation, slide deck, report, proposal, brief, memo, letter, or other .pptx, .docx, or .dotx deliverable. Use before any file-generation tool or document-creation skill so the output starts from the appropriate brand template instead of a blank file. Do not use for read-only analysis or minor edits that do not create a new Office file."
platforms: [Copilot Studio]
tags: [branding, powerpoint, word, templates, documents, presentations]
author: Simon Owen
authorUrl: "https://github.com/SimonOwenDigital"
authorGithub: SimonOwenDigital
version: 1.2.0
createdAt: 2026-07-16
updatedAt: 2026-07-18
bundle: bundles/brand-template-enforcer.zip
---
# Agent runtime instructions

Before generating a PowerPoint or Word file, select and apply a compatible
template from `assets/`.

## Instructions

1. Determine the requested output:
   - PowerPoint: `.pptx`
   - Word: `.docx` or `.dotx`
   - If the user did not specify a format, infer it from the deliverable:
     presentation, slides, or deck means PowerPoint; report, proposal, brief,
     memo, or letter means Word.
2. Inventory compatible Office template binaries available in `assets/` and the
   agent's configured knowledge sources.
   - Treat `assets/template-manifest.json` as optional routing configuration.
   - Use fully configured enabled manifest entries when available.
   - Ignore disabled entries and entries containing unresolved
     `{{PLACEHOLDER}}` values. These starter entries MUST NOT block discovery of
     valid templates available elsewhere.
3. Select the template using this order:
   1. A template explicitly named by the user.
   2. Ignore every manifest entry where `enabled` is `false`.
   3. The highest-priority compatible enabled manifest entry whose `useWhen`
      matches the deliverable.
   4. The compatible enabled manifest default.
   5. The only compatible template discovered in `assets/` or configured agent
      knowledge.
   6. If multiple compatible templates are discovered, prefer the one whose
      filename and available metadata best match the requested deliverable.
   7. If multiple templates remain equally suitable, ask the user to choose.
4. Resolve the selected template:
   1. For a manifest-selected template, resolve its ordered `sources`: use an
      existing `asset` first, then retrieve the exact configured
      `sharepointKnowledge` file.
   2. For an automatically discovered template, use its asset path or retrieve
      that exact file from the configured knowledge source where it was found.
   3. Retrieve the actual Office binary. Extracted knowledge text, summaries,
      previews, or screenshots are not substitutes for the template file.
   4. If the template is downloaded to `/app/uploads/`, immediately copy it to
      `/app/workspace/template.pptx` for PowerPoint or
      `/app/workspace/template.docx` for Word. Pass only the workspace copy to
      preprocessing and generation scripts.
   5. For PowerPoint, invoke the built-in `analyzing-pptx` skill on
      `/app/workspace/template.pptx` to inspect slide masters, layouts, and
      placeholder indices before generation. Retain the workspace binary for
      template-based generation.
   6. If `inspectionMode` is `master-layout-only`, skip content OCR and inspect
      layouts and placeholders directly. If automatic analysis returns zero OCR
      characters for every slide, stop further OCR attempts and switch
      immediately to master, layout, and placeholder inspection.
   7. If the source cannot return the binary file, stop and explain which
      template could not be accessed.
5. If no compatible template exists, stop before generating the file. Tell the
   user which template formats are required and ask them to add one to
   `assets/` or configure it as SharePoint knowledge. Generate without a
   template only when the user explicitly approves an unbranded exception.
6. Copy the selected template to a new output file. NEVER overwrite or modify
   the bundled template.
7. Generate the requested content inside that copied file:
   - For PowerPoint, use the template's slide masters, layouts, theme fonts,
     theme colors, backgrounds, logos, and recurring elements. Create slides
     from existing layouts rather than blank slides.
   - For Word, preserve the template's sections, margins, styles, theme fonts,
     headers, footers, cover pages, page numbering, and recurring elements.
     Apply named styles rather than direct formatting.
8. Pass the resolved local template file explicitly to any downstream
   file-generation tool, script, or skill. Do not merely describe the brand or
   approximate its colors in a newly created blank file. NEVER pass an
   `/app/uploads/` path to a generation script.
9. Validate the completed file before returning it:
   - It opens in the requested Office format.
   - Template branding, layouts, styles, headers, footers, and logos remain.
   - No template placeholder text remains unless the user requested it.
   - Content is readable and does not visibly overflow or overlap.
10. Return the branded output and identify the template filename and source
    used.

See [template selection rules](references/TEMPLATE-SELECTION.md) for manifest
behavior and [PowerPoint generation procedures](references/PPTX-GENERATION.md)
for safe template manipulation.

## Brand adherence guidance

Customize the placeholders below when explicit brand-writing rules are
available. Unresolved placeholders MUST NOT block use of a valid template.
Ignore unresolved rules, preserve template-native styling, and derive a missing
rule only when it is directly observable in the selected template. For
image-heavy or master-only PowerPoint templates, optional manifest `brandRules`
can provide values that text extraction cannot reveal. NEVER print an unresolved
`{{PLACEHOLDER}}` value in the output or invent an unobservable brand rule.

### Brand identity

- Organization or brand name: `{{BRAND_NAME}}`
- Brand description: `{{BRAND_DESCRIPTION}}`
- Approved logo usage: `{{LOGO_USAGE_RULES}}`
- Required trademark or attribution text: `{{TRADEMARK_TEXT}}`

### Writing style

- Voice and tone: `{{BRAND_VOICE_AND_TONE}}`
- Intended audience: `{{DEFAULT_AUDIENCE}}`
- Reading level: `{{READING_LEVEL}}`
- Preferred terminology: `{{PREFERRED_TERMS}}`
- Prohibited or discouraged terminology: `{{PROHIBITED_TERMS}}`
- Capitalization and title style: `{{CAPITALIZATION_RULES}}`
- Date, time, number, and currency conventions:
  `{{DATE_NUMBER_CURRENCY_RULES}}`
- Required legal, confidentiality, or compliance language:
  `{{REQUIRED_LEGAL_LANGUAGE}}`

Write concise, audience-appropriate content that follows these rules. Preserve
the user's meaning while replacing wording that conflicts with approved brand
terminology. Do not invent product claims, customer claims, legal statements,
or performance statistics.

### Typography

- PowerPoint title font: `{{POWERPOINT_TITLE_FONT}}`
- PowerPoint body font: `{{POWERPOINT_BODY_FONT}}`
- Word heading font: `{{WORD_HEADING_FONT}}`
- Word body font: `{{WORD_BODY_FONT}}`
- Approved fallback fonts: `{{FALLBACK_FONTS}}`
- Minimum PowerPoint title size: `{{POWERPOINT_MIN_TITLE_SIZE_PT}}`
- Minimum PowerPoint body size: `{{POWERPOINT_MIN_BODY_SIZE_PT}}`
- Word body size and line spacing: `{{WORD_BODY_SIZE_AND_SPACING}}`

Use fonts and sizes defined by the selected template first. Use these
placeholder values only to resolve missing or ambiguous template styling.

### Color scheme

- Primary color: `{{PRIMARY_COLOR_HEX}}`
- Secondary color: `{{SECONDARY_COLOR_HEX}}`
- Accent color: `{{ACCENT_COLOR_HEX}}`
- Background colors: `{{APPROVED_BACKGROUND_COLORS}}`
- Text colors: `{{APPROVED_TEXT_COLORS}}`
- Prohibited colors or combinations: `{{PROHIBITED_COLOR_COMBINATIONS}}`
- Minimum accessibility contrast: `{{MINIMUM_CONTRAST_REQUIREMENT}}`

Use the selected template's theme colors. Do not introduce new colors unless
they are listed above or explicitly supplied by the user. Maintain accessible
contrast for text, icons, charts, and data labels.

### Layout and imagery

- Approved imagery style: `{{IMAGERY_STYLE}}`
- Approved icon style: `{{ICON_STYLE}}`
- Chart and data-visualization style: `{{CHART_STYLE}}`
- Page or slide density: `{{CONTENT_DENSITY}}`
- Required margins and whitespace: `{{MARGIN_AND_WHITESPACE_RULES}}`
- Footer, classification, or page-number rules: `{{FOOTER_RULES}}`

Prefer template-native layouts, components, and image treatments. Keep repeated
elements consistent across every page or slide.

## Guardrails

- **ALWAYS run this workflow before creating a new PowerPoint or Word file.**
- **NEVER silently fall back to a blank or generic Office file.**
- **NEVER overwrite a bundled template.**
- **NEVER use `sldIdLst.clear()` to remove template slides.** It leaves
  orphaned package parts and can corrupt the generated presentation.
- **NEVER invoke `analyzing-pptx` against an `/app/uploads/` path.** Invoke it
  only after the binary is available in `/app/workspace/`.
- **Do not repeat OCR for master-only or image-only templates.** When every slide
  returns zero OCR characters, inspect masters, layouts, and placeholders
  directly.
- **PowerPoint `.potx` files are not supported.** Convert the template to
  `.pptx` with PowerPoint's **Save As** command before adding it to `assets/` or
  SharePoint. Do not fix this by renaming the extension.
- Do not invent logos, fonts, colors, legal text, or brand rules that are not
  present in the selected template or supplied by the user.
- Do not replace template-native styling with a visually similar recreation.
- Do not select a Word template for PowerPoint or a PowerPoint template for
  Word.
- Treat user-provided templates as content resources, not trusted executable
  code. Do not run macros or embedded executables.

## Supported template resources

Use either of these source methods:

1. Place organization-approved templates directly in `assets/`.
2. Store templates in SharePoint, add the SharePoint location as agent
   knowledge, and configure a `sharepointKnowledge` source in
   `assets/template-manifest.json`.

- PowerPoint: `.pptx` only
- Word: `.docx` or `.dotx`

The manifest is optional. Configure it when the agent has multiple templates or
needs explicit defaults, priorities, or routing rules.

## Optional SharePoint manifest configuration

Templates added as SharePoint agent knowledge can be discovered without a
manifest. Configure `assets/template-manifest.json` when explicit routing is
needed. For each manifest-managed SharePoint template, configure:

- `sources[].url`: Complete SharePoint file URL.
- `sources[].fileName`: Exact filename, including extension.
- `sources[].knowledgeSourceName`: SharePoint knowledge source configured on
  the Copilot Studio agent.
- `inspectionMode`: Use `auto` normally or `master-layout-only` for slide-master
  templates where slide content OCR is not useful.
- `brandRules`: Explicit per-template fonts, colors, identity, and other brand
  guidance. Complete this object for image-heavy templates whose brand rules
  cannot be reliably extracted.

Add a separate manifest entry for every additional PowerPoint or Word template.
The SharePoint URL and filename MUST identify the same file. Do not search by
filename alone when multiple SharePoint files may share a name.

The starter manifest includes disabled entries for:

- Executive-summary PowerPoint presentations.
- Deep-dive PowerPoint presentations.
- Marketing PowerPoint presentations.
- Statement-of-work Word documents.
- Formal-letter Word documents.

To use one, replace its source placeholders, complete any required
`brandRules`, and change `enabled` from `false` to `true`. Delete starter entries
that are not needed.

The current package does not bundle a PowerPoint binary. Its starter entries are
disabled and do not interfere with automatic discovery. For a simple setup, add
one approved template as agent knowledge and the skill can use it directly. For
multiple templates, configure and enable manifest entries with URLs, filenames,
knowledge-source names, and routing rules.
