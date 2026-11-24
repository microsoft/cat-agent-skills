# Evidence-led design

An editorial light/dark language: open evidence fields, substantial visuals,
short assertions and related Blue/Cyan/Teal/Aqua accents. One primary pattern
organizes each page; preserve its relationships while adapting content, not the
source's identity. Read `patterns.md` for composition and emphasis, then
`layouts.md` for aspect suitability.

## Theme and canvas

`evidence-led.tokens.json` supplies the default palette and semantic roles.
Explicit user brand/style takes precedence over its literal values. Map ink,
inverse-ink and on-accent to each actual light, dark or image surface; a white
canvas token does not prohibit dark/image pages. Use ink on white/light fields,
structure for hierarchy, primary and series-1..5 for related data, accent-ink for
colored text, and neutral roles for alternatives/Others. Red/amber/green statuses
require a supported meaning and a direct label. A positive amount is not a
success status. Solid quantitative marks preserve scale; a restrained native
gradient may connect a timeline or support a photo.

The five core donors have a clean internally authored theme/master. A practical
default is to start from a selected core donor, remove its sample slide/content
and retain the linked theme/master as the deck seed. This is a component, not a
full-page template. User-supplied branding wins and must reach explicit colors
and fonts as well as theme slots.

The linked Office theme uses dk1/lt1 = ink/canvas, dk2/lt2 = muted/surface,
accent1..6 = series-1..5/accent-ink, hlink = structure, folHlink = accent-ink.
Major Latin is Aptos Display; minor Latin is Aptos, with Arial fallback. For
Chinese use an available Microsoft YaHei or Noto Sans CJK SC and inspect export.
Follow presentation, slide-layout and slide-master relationships to actual theme
parts using `pptx/SKILL.md` and
`pptx/editing.md`. Read back `a:clrScheme` and `a:fontScheme`
in the authoritative deliverable. Font-only generator settings or literal RGB
styling do not prove a linked color theme.

Default canvas: **12,192,000 × 6,858,000 EMU**. PptxGenJS `LAYOUT_16x9` is
10 x 5.625 inches, not this physical canvas. A user template can override size;
keep imports and coordinates consistent.

## Typography and fit

Ordinary text is **at least 14pt**: body, diagram labels, dates, captions,
definitions, scope and conditions. Genuine chart/table labels are **at least
10pt**, preferably larger. Classify by meaning, not object type; diagram text
does not become a chart label because it sits beside a chart. Measure effective
size after inherited fonts, group scaling, autofit and substitution.

Use larger type for the focal number, keyword or assertion, with its unit and
definition immediately adjacent. Avoid redundant subtitles and reserved footnote
bands. Keep necessary scope beside evidence. Enlarge useful content, reflow
actual item counts or cut repetition before reducing type. Circle/icon scaling
must stay uniform; separate text reflow from graphic scaling. Purposeful whitespace
is not an invitation to invent content.
Fit donor nodes, connectors, headings and body regions as one component; replace
overlapping placeholder boxes and check clearance after wrapping. Give each
region enough room before shortening copy or splitting a substantive argument.
Small type and deleted defining icons are not fit repairs.

## Composition and surfaces

Every non-agenda page has a meaningful visual focus. Cover and relationship
close use actual relevant full-image imagery by default; body pages may use a picture, native chart/table,
infographic, semantic icon relationship or supported large number/keyword.
Undifferentiated paragraphs, an empty panel or a decorative rule do not qualify.
Preserve the selected pattern's hierarchy and topology: aligned paired rails,
round icon nodes on a continuous spine, directed arrows, real table intersections.
Do not dissolve them into equal rounded cards.

Open compositions are the default. No external container border or faux
elevation; keep meaningful axes, arrows, tracks and table separators. Where a
pattern uses evidence frames, use one consistent fill/stroke/corner treatment
throughout the deck. Ordinary frames use an 8px corner radius (76,200 EMU at
96dpi); circles, arrowheads, capsule duration bars and full-bleed images are
semantic exceptions. Do not add a frame around every donor.

Keep 4.5:1 ordinary-text and 3:1 large-text/meaningful-graphic contrast against
the actual local background. Pale fills need dark ink. Deep fields can carry
white. Recheck images, gradients and recolored shapes. Panels must not obscure
labels; adjacent text regions need visible separation.

## Meaningful images

Apply `../SKILL.md`'s restrictions first. Plan full-image cover and relationship
close slots unless the user explicitly directs otherwise. Body-slide image
count follows explanatory need, not a universal quota. Use imagery for
product/company context, applications, cases or transitions in customer pitches.
Use `image/SKILL.md`, `renderTextInImage=false`, and its
provider/Ghostrider batching and join rules. Generate, join, inspect and place
the returned images; prompts and successful jobs without placement are not enough.

Plan subject position, quiet text region, active user style and aspect ratio.
Provider composition rules take precedence over Sales crop/overlay patterns.
For Ghostrider, request the measured full-slide slot and quiet contrast-safe
space, then scale the slot-ready result without cropping, masking, recoloring,
or adding `a:srcRect`. Do not assume overlays are allowed: use them only where
the active Image Skill/provider permits; otherwise request suitable contrast
in the image composition and keep text editable under its placement rules.
For other sources, use subject-aware crops only with permission; never stretch.
Authorized source imagery
establishes actual identities; generated scenes are context, not proof of real
UI, staff, customer identity, endorsement or an occurred event. Keep titles,
numbers, masks and data native and editable. Use coherent licensed icons through
shared SVG tooling such as `native_svg_icon`, not font glyphs or improvised
primitive-shape icons. Number badges express order, not semantic icon meaning.

When the request specifies a picture fraction `f`, verify at least `ceil(N × f)`
distinct picture-bearing pages using final page count `N`. Count pages, not
objects; icons, charts, logos and negligible stamps do not count. Recalculate
after page-count changes. Requested full-bleed means visibly edge-to-edge imagery,
not a full-size image hidden behind an opaque panel. Where permitted, native dark
overlays with explicit alpha stops can support light text while leaving the subject visible.
The same relevant image may serve both endpoints; an icon, logo, chart or shape
background cannot replace it. Template-search failure or removal of an imagery
question is not image-provider failure or an explicit no-image choice.
Follow allowed provider fallbacks and inspect actual results. If required images
remain unavailable, report BLOCKED; do not claim a shape-only redesign satisfies
the image requirement. Never fabricate logos, private content or contact details.

## Native data and final audit

Read the selected family contract, including for original native compositions.
Native shapes are editable but do not imply Excel Edit Data. Quantitative edits
must update data, labels, geometry, caches and workbooks together; preserve
material precision and distinguish observation, target, forecast and proposal.

Apply `../SKILL.md`'s final-file closure after normalization. Inspect every final
render, visible label/cell and permitted note against the complete source:
pattern hierarchy, semantic geometry, linked theme, effective font floors,
contrast, image identity/placement, scope and human gates. Font XML and package
validity alone are not visual proof; unresolved fit remains unknown. Recheck the
authoritative file after any repair, not an unused copy or earlier preview.
Record the renderer and actual resolved/substituted fonts. A font-substituted
render proves fit only in that renderer, not native PowerPoint fidelity; mark
native fidelity unverified until observed. Visible overlap is a failed fit gate,
even when pack reports no warnings.
