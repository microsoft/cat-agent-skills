# Worked example: Contoso Q3 review onto the Contoso brand template

A full run on generated sample files. Contoso Field Services is fictional; every number is illustrative.

## The request

"Here is our Q3 review deck and the new Contoso brand template. Put the deck on the template."

## 0. Generate the sample files

```bash
python SKILL_DIR/scripts/make_samples.py --out-dir working/contoso/in
```

- `contoso-q3-review.pptx`: 11 slides, 4:3, default Office look. Title, section, bullets on three
  levels, two columns, comparison, a table with a purple header fill, a column chart with custom colors,
  a picture with caption, a 12-bullet slide, a free-form slide (three colored shapes, a grouped picture
  and label, a large text box as title) and a closing slide with a web link. Notes on every slide.
- `contoso-brand-template.potx`: 16:9, teal and navy theme, Georgia headings and Verdana body, a teal
  bar and footer on the master, nine renamed layouts (one with no layout type), a dark section layout
  and three sample slides with sample text.
- `contoso-color-sheet.pptx`: one slide of swatches and a Blank layout only (for the fallback).

## 1. Inspect

```bash
python SKILL_DIR/scripts/inspect_decks.py --template working/contoso/in/contoso-brand-template.potx \
  --source working/contoso/in/contoso-q3-review.pptx --json-out working/contoso/inspect.json
```

Result: 9 layouts classified (Cover = title, Content = content, Divider = section, Two Column =
two_content by its placeholders, Compare = comparison, Headline Only = title_only, Clean = blank,
Content and Caption = caption_content, Photo = picture). Recommended mode: rebuild. On the source side,
slide 6 (Title Only plus a table) and slide 7 (a chart) read as content, and slide 10 (Blank) reads as
title_only because its large top text box becomes the title.

## 2. Plan and approval

```bash
python SKILL_DIR/scripts/plan_mapping.py --template working/contoso/in/contoso-brand-template.potx \
  --source working/contoso/in/contoso-q3-review.pptx \
  --json-out working/contoso/mapping.json --md-out working/contoso/mapping.md
```

All 11 slides find an exact match (see `assets/example/mapping.example.json`). The table goes to the
user with "Want to change any of these?". Example override, if the user wants the rollout slide on the
clean layout: `--override "10=Contoso Clean"`. The title then goes into a text box in the heading font
and the shapes move below it.

## 3. Build

```bash
python SKILL_DIR/scripts/apply_template.py --mapping working/contoso/mapping.json \
  --out working/contoso/contoso-q3-review-on-template.pptx --report-out working/contoso/build.json
```

11 slides out, 7 fixes, no warnings, no overflow:
- 3 template sample slides removed.
- Slide 4 title 44 to 42 pt; slide 9 body 32 to 22 pt.
- Table rebuilt in the themed style (teal header instead of the hard-coded purple).
- Chart rebuilt from its data, series in accent 1 and 2.
- Picture fitted in the photo area.
- Slide 10 shapes scaled into the content area; their colors mapped to accent 1, accent 6 and accent 3.

Text, bullet levels and notes match the source on every slide.

## 4. Split test (optional)

With a higher body floor the long slide no longer fits:

```bash
python SKILL_DIR/scripts/apply_template.py --mapping working/contoso/mapping.json \
  --out working/contoso/tight.pptx --body-floor 22
# OVERFLOW slide 9: text still overflows at the 22 pt floor ...
```

After the user agrees: `--split-overflow 9` gives 12 slides; slide 10 is "Lessons learned from the
pilot (continued)" with the last five bullets.

## 5. Visual QA

```bash
python SKILL_DIR/scripts/deck_qa.py working/contoso/contoso-q3-review-on-template.pptx \
  --out-dir working/contoso/preview --template working/contoso/in/contoso-brand-template.potx \
  --source working/contoso/in/contoso-q3-review.pptx --json-out working/contoso/qa.json
```

Lint: 0 FAIL, 0 WARN. One contact sheet. Seen on the sheet: teal bar and footer on every slide, white
title on the navy divider, bullets indented as in the source, table and chart in theme colors, picture
unstretched, no sample text.

## 6. Fallback on the color sheet

```bash
python SKILL_DIR/scripts/plan_mapping.py --template working/contoso/in/contoso-color-sheet.pptx \
  --source working/contoso/in/contoso-q3-review.pptx --json-out working/contoso/map-cs.json
# Mode: restyle (fallback) ...
python SKILL_DIR/scripts/extract_brand.py working/contoso/in/contoso-color-sheet.pptx --json-out working/contoso/brand.json
python SKILL_DIR/scripts/restyle.py --source working/contoso/in/contoso-q3-review.pptx \
  --brand working/contoso/brand.json --out working/contoso/contoso-q3-review-restyled.pptx \
  --report-out working/contoso/restyle.json
```

The copy keeps its 4:3 layouts, takes Georgia and Verdana and the Contoso colors, maps 13 hard-coded
colors to theme slots and shrinks the text that the wider brand fonts pushed out of its boxes. Lint:
0 FAIL.

## 7. Report

See `assets/example/summary.example.md`, plus the line on what the contact sheet showed.
