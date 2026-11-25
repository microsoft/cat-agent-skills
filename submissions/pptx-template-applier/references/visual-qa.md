# Visual QA

The build is not done until the lint passes and every contact sheet has been looked at.

## 1. Run it

```bash
python SKILL_DIR/scripts/deck_qa.py <out>.pptx --out-dir working/<slug>/preview \
  --template <template> --source <deck> --json-out working/<slug>/qa.json
```

`--template` lets the lint catch the template's own sample text. `--source` stops text that the source
deck itself contains from being flagged.

## 2. Lint checks

| Level | Check | Meaning | Usual fix |
|---|---|---|---|
| FAIL | off_slide | a shape runs outside the slide | override the slide to a layout with more room, or rebuild; free content is scaled to fit, so this usually means a copied shape was already off the source slide |
| FAIL | overflow | text needs clearly more height than its box | split (with the user's yes) or ask the user to shorten |
| FAIL | leftover_text | "Click to add title", "Lorem ipsum", "Sample text", or a line from the template's sample slides | find where it came from (usually a shape copied from a source that was itself built on the template) and remove it from the output |
| FAIL | contrast | text under WCAG AA: 4.5:1, or 3:1 for 18 pt and up or 14 pt bold and up | map the slide to a layout with a light background, or tell the user which shape color to change |
| WARN | overflow_risk | text is close to filling its box | check that slide on the render |
| WARN | overlap | two shapes overlap, or a shape covers template decor (bar, logo, footer) | check the render; move or override the layout if it looks wrong |
| WARN | empty_placeholder | a placeholder with no text | normally removed by the build; remove it if it remains |
| WARN | small_font | under 12 pt (10 pt in tables) | accept for footnotes, otherwise split or shorten |
| WARN | no_notes | no speaker notes | only a problem if the source slide had notes |

Contrast is computed only where the background is a known solid color (shape fill, slide, layout or
master background). Text on pictures or gradients is not measured: look at it on the render.

## 3. Look at every contact sheet

The script writes `contact-1.png`, `contact-2.png` and so on, 12 slides each. Open every one with the
image viewer. For each slide, check:

- Text cut off at a box edge or running past the slide.
- Text over a picture, a shape or the template's bar, logo or footer.
- The title in the heading font and the body in the body font of the template.
- Bullet levels indented as in the source.
- Tables readable, header row in the template accent, no overflow below the slide.
- Charts with their legend and labels, colors from the template.
- Pictures in place, not stretched.
- No "Click to add", sample or lorem text.
- Dark layouts (for example a section divider) with light text.

Write one line per slide that needs attention. If the sheets are hard to read, render at a higher
`--dpi` (90) or fewer slides per sheet (`--per-sheet 6`).

## 4. Fix loop

Fix, rebuild, rerun the QA. At most two passes. If a FAIL is still standing, report it with the slide
number and do not call the deck ready.

## 5. Without rendering tools

When soffice or pdftoppm is missing, `deck_qa.py` runs the lint and says so (`render_note`). Report:
"I could not render the slides here, so the visual check is lint only. Please open the deck and look at
each slide."
