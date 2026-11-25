# PowerPoint Template Applier

Give it an existing deck and your brand template, and get back the same deck rebuilt on the template. Each slide lands on the right layout and picks up the template's theme colors and fonts. Your titles, bullet levels, tables, charts, images, speaker notes and slide order stay as they were. Your original files are never changed.

## What you get

- **A rebuilt deck:** a new .pptx on your template's slide masters and layouts, with the template's sample slides removed.
- **A layout plan first:** a table that maps every slide to a template layout with the reason, so you can change any row before the build.
- **Text that fits:** text shrinks in small steps down to readable floors (title 24 pt, body 14 pt, table 10 pt). Slides that still overflow are flagged, and they are split into continuation slides only if you agree.
- **A visual check:** every slide is rendered and reviewed on contact sheets for clipped text, overlaps, leftover sample text and poor contrast before the deck is called ready.
- **A short report:** slides converted, the layout mapping, fixes made and anything a person should check by hand.

## Works with any kind of brand file

- **A full template** (.pptx, .potx or .potm) with masters and layouts: full rebuild on its layouts.
- **A color sheet or logo page** with no usable layouts: a fallback mode restyles a copy of your deck with the brand's theme colors and fonts and maps hard-coded colors to the brand palette.
- **Different slide sizes:** 4:3 decks move onto 16:9 templates.

## Example prompts

- "Apply our brand template to this deck."
- "Move these slides onto the new company template."
- "Our brand file is only a color sheet. Make this deck match it."
- "Convert my old 4:3 deck to the new 16:9 template, and put slide 5 on the two column layout."

## What you need

- Python 3 with python-pptx, lxml and Pillow.
- Optional: LibreOffice and pdftoppm for the rendered visual check. Without them, a layout lint runs and the report asks a person to check each slide.
- Optional: Microsoft 365 file tools to fetch decks from OneDrive or SharePoint.
- Works offline on local files. The bundled scripts do the whole job, so no other skill is required.

## Good to know

- **Content stays faithful.** No rewording, no dropped slides, no invented text. The only text it adds is "(continued)" on continuation slides you approved.
- **Some items need a manual copy.** Scatter, bubble and combo charts, SmartArt and embedded objects are listed in the report for you to copy by hand.
- **Try it with sample files.** A bundled script generates a fictional Contoso deck, brand template and color sheet so you can see a full run.
- **Files only.** It never sends, posts, shares or uploads anything.
