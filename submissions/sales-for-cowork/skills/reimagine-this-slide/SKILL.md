---
name: reimagine-this-slide
description: 'Builds three genuinely different, non-destructive alternatives of one existing PowerPoint slide so the user can pick a real slide instead of describing one; each adds meaning (comparison, benchmark, insight, better visual), not just reformatting. Use when working on one slide and asking for other ways to communicate its point: "reimagine this slide", "give me three slide ideas", "how else could I show this?". Also for a selected text, chart, or image ("reimagine this chart"). Do NOT use for copy editing, pure chart restyling, multi-slide deck creation, or simple moves/resizes.'
metadata:
  displayName: "Reimagine this slide"
---

# Reimagine This Slide

Create three genuinely different, non-destructive alternatives to the current
slide or selection. Each alternative must make the point easier to understand by
adding context, comparison, insight, or a better visual form; merely rearranging
the same content is not ideation.

## When to use

Use this for one slide or a selected text, chart, or image when the user asks for
ideas, a stronger story, another way to show something, or the "so what."

Do not run the three-slide workflow for typo fixes, copy editing, cosmetic chart
restyling, simple moves or resizes, or requests to create a multi-slide deck. If
the intended point is genuinely unknowable, ask one clarifying question and stop.
If the user explicitly asks for one alternative, build one.

Selection handling: adapt to what is selected. Text gets a sharper takeaway or
comparison; a chart gets a better-fit chart or an anchoring comparison; an image
gets a visual that carries the point; with nothing selected, work on the whole
slide. If none of the three alternatives land, offer more ideas.

## Critical output contract

- Read the current deck from `$WORKSPACE_DIR/input.pptx`.
- Preserve the source slide and every pre-existing slide. Insert the alternatives
  as one consecutive block immediately after the source unless the user explicitly
  asks to replace it on a follow-up turn.
- Edit with the installed `python-pptx`. Do not extract or rebuild the OOXML
  package, install dependencies, or rely on a harness-specific presentation tree.
- Save the completed deck to `$OUTPUT_DIR/output.pptx`; another filename may not be
  delivered.
- In **Keep the content** mode, preserve every main point and every source figure;
  supporting detail may move to notes but must not disappear.
- In **Rework the story** mode, preserve the core message and factual accuracy;
  supporting content may be rewritten, combined, or omitted, but retained figures
  must stay exact and no fact or replacement figure may be invented.
- Added comparisons must be grounded and clearly approximate; unresolved external
  facts stay visibly marked for confirmation.

## Workflow

1. **Set the content freedom before doing any analysis.** If the user has not
   already made the choice unambiguously, ask:

   **How much freedom should I take with the content?**

   - **Keep the content** — Preserve every main point, fact, and figure.
     Supporting detail may be condensed or moved to speaker notes.
   - **Rework the story** — Keep the core message and factual accuracy, but
     freely rewrite, combine, or omit supporting content to make the point land.

   Ask with the host's supported user-question mechanism when it is available;
   otherwise ask in chat. Stop and wait for the answer. Do not identify
   directions or build slides until the user answers. Record **Keep the content**
   as `strict` and **Rework the story** as `broad`, state which mode is active,
   and use it for all three alternatives.

2. **Identify the target and its point.** Determine whether the user selected
   text, a chart, an image, or the whole slide. Read
   `references/representation-menu.md` for that branch. State internally the one
   takeaway and what prevents it from landing.

3. **Choose three distinct directions.** Each direction must add meaning rather
   than only restyle the source. For a statistic, read
   `references/anchor-library.md` and verify any external comparison with an
   available search source; if search is unavailable, use deck-grounded context
   or a transparent confirmation placeholder instead of inventing a fact. Mix
   approaches when useful rather than producing three cosmetic variants.

4. **Build the alternatives.** Read `references/build-recipes.md` as needed, then
   open the input deck with `python-pptx` and add editable slides after the source.
   Match the deck's dimensions, fonts, palette, spacing, and visual treatment.
   In particular, a flat source deck stays flat: do not introduce shadows,
   gradients, bevels, or other effects absent from the existing deck. Use a
   presentation-ready title that states the takeaway, not an internal technique
   label. Keep one clear focal point, avoid an accent rule under the title, and
   preserve provenance and unresolved facts in speaker notes. In **Keep the
   content**, move useful trimmed detail into notes rather than deleting it. In
   **Rework the story**, keep useful presenter context in notes and track any
   supporting detail intentionally omitted for the handoff.

5. **Save and inspect.** Write `$OUTPUT_DIR/output.pptx`. View or render the three
   slides and compare them with the source for theme continuity, balance,
   clipping, and whether each visual actually communicates the intended object or
   comparison. Do not size text from server-rendered font metrics.

6. **Run the bundled verifier for each alternative.**

   ```bash
   python3 "$SKILLS_DIR/reimagine-this-slide/scripts/verify_slide.py" \
     --deck "$OUTPUT_DIR/output.pptx" --source N --built M --expected-offset K \
     --content-mode strict
   ```

   Pass `strict` for **Keep the content** and `broad` for **Rework the story**.
   Use offsets 1, 2, and 3. `REIMAGINE_THIS_SLIDE_VERIFY_OK=1` means the automated
   checks passed. Any nonzero exit or
   `REIMAGINE_THIS_SLIDE_VERIFY_ERR_REASON=...` is a hard stop: correct the deck
   and rerun. In broad mode, read `allowed_omissions`, verify each item is
   genuinely supporting rather than core, and name those omissions in the
   handoff. Read `not_checked` and inspect those properties manually; the script
   does not prove source-slide identity, theme colors, image-embedded numbers, or
   semantic quality.

7. **Hand back the choices.** Summarize the three alternatives by their
   presentation-ready titles and one-line differences, name the active content
   mode, mention any unresolved facts, and ask whether to keep one, refine one, or
   try three fresh directions. In **Keep the content**, mention any supporting
   detail moved to notes. In **Rework the story**, mention supporting content
   moved, combined, or omitted. Do not narrate the workflow.

## References

Load only what the current case needs:

| File | Use |
|---|---|
| `references/representation-menu.md` | Candidate directions for text, chart, image, or whole-slide selections |
| `references/anchor-library.md` | Starting points for grounded scale comparisons |
| `references/build-recipes.md` | Theme, layout, notes, insertion, and rollback guidance |
| `references/worked-examples.md` | Executed examples and guard cases |
| `references/troubleshooting.md` | Ambiguity, missing capabilities, and verifier failures |
| `scripts/verify_slide.py` | Read-only checks against the completed deck |
