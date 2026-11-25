# Fallback: restyle a copy of the source

Use this mode when the brand file has no usable layouts: `inspect_decks.py` prints
`Recommended mode: restyle` and `plan_mapping.py` writes `"mode": "restyle"`. Typical cases are a brand
deck that is one color sheet, a logo page, or a set of blank slides.

## Steps

1. Get the brand values from the template's theme:
   ```bash
   python SKILL_DIR/scripts/extract_brand.py <brand file> --json-out working/<slug>/brand.json
   ```
   Check `colors` and `fonts`. If they are the default Office values (Calibri, accent 1 `#4472C4` or
   `#4F81BD`) but the brand file shows colored swatches, run again with `--from-swatches`. That takes
   accent 1 to 6 from the filled shapes on its slides, in order of first use. Show the user the six
   colors and ask whether the order is right. The user can also give hex values: edit `brand.json`.
2. Restyle a copy:
   ```bash
   python SKILL_DIR/scripts/restyle.py --source <deck> --brand working/<slug>/brand.json \
     --out working/<slug>/<name>-restyled.pptx --report-out working/<slug>/build.json
   ```
   What changes:
   - The color and font scheme of every theme the deck uses becomes the brand's.
   - Hard-coded colors in slides, layouts, masters and charts map to theme slots (same rules as the
     rebuild, `build-and-fit.md` section 3).
   - Hard-coded font faces on slides are removed so the theme fonts apply.
   - Placeholder text that no longer fits with the brand fonts is shrunk down to the floors.
   What does not change: layouts, positions, backgrounds that are pictures, animations, content.
3. Run the visual QA (`visual-qa.md`) on the restyled copy, then the summary without `--mapping`:
   ```bash
   python SKILL_DIR/scripts/summarize_run.py --build working/<slug>/build.json --qa working/<slug>/qa.json
   ```

## Tell the user

- That the template had no usable layouts, so the deck kept its own layouts and took the brand colors
  and fonts.
- Which colors were used and, with `--from-swatches`, that the accent order is a best guess.
- That a template with real layouts gives a closer match, if they can find one.
