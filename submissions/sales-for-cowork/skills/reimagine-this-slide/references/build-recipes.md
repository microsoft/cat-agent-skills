# Build recipes

How to construct each of the three directions in workflow step 4. Read this after
the directions are selected internally and before building the slides.

---

## 1. Building the slide

Open `$WORKSPACE_DIR/input.pptx` with the container's installed `python-pptx`.
Preserve the source slide and construct the three alternatives as a consecutive
block immediately after it — titles, text, charts, shapes, images, and speaker notes.
Do not extract or rebuild the OOXML package or install packages at runtime.

**Expected output:** `$OUTPUT_DIR/output.pptx`, containing new slides at positions
*n+1*, *n+2*, and *n+3*. The host delivers that file. Never claim a slide was built
when it wasn't saved there.

Two things stay code-free but deliberate:

- **Charts** are native charts, not images of charts — the user needs to edit them.
- **The source slide is never touched.** You're adding a slide, not rewriting one.

The one bundled script is `scripts/verify_slide.py`, used in step 5 to check the
saved deck. The model may write a task-specific workspace script to perform the
`python-pptx` edits; the bundled verifier remains read-only.

## 2. Reading the deck's theme

Never guess the theme. In priority order:

1. **Slide master / theme part** — take the two dominant theme colors (one dominant,
   one accent) and the major (heading) and minor (body) typefaces.
2. **The source slide itself** — if the master is unreadable, use the source slide's
   title font, its body font, and its most-used non-black, non-white fill as the accent.
3. **Neutral fallback** — a near-black text color, a white background, and a single
   accent sampled from any chart or shape on the source slide. **Tell the user** you
   couldn't read the theme and are approximating. If the source carries no color at
   all, stay monochrome and let size contrast do the work — a monochrome slide that
   lands beats an invented brand color.

Carry over: fonts, the two colors, the slide dimensions (16:9 vs 4:3), and every
footer artifact from the source slide. Keep the source footer text,
confidentiality or classification marking, date, and slide number in the same
footer placeholders and positions on all three alternatives. Do not replace them
with a design label or omit the number. The body must still use a new layout — the
whole point is a new way to communicate the slide's content.

## 3. Apply the selected content mode

Use one mode for all three alternatives.

### Keep the content (`strict`)

- Preserve every main point, fact, and figure.
- Supporting detail may be condensed, reorganized, or moved to speaker notes.
- Nothing from the source may be silently deleted.

### Rework the story (`broad`)

- Preserve the core message and factual accuracy.
- Supporting text and supporting figures may be rewritten, combined, or omitted.
- Any retained figure stays exact; never substitute, alter, or invent a figure.
- Record moved, combined, and omitted content for the final handoff.

Both modes preserve the source slide, insertion order, footer artifacts, and
anchor-visual requirements.

## 4. Anchor visual — make it rich, then fall back

Every direction requires the anchor to be **shown**, not just named — and shown
*well*. This is a visual medium; a detailed illustration is part of the idea landing.
Use the highest rung you can produce. **Never skip the visual and ship a naked
number** — degrade down the chain instead, but start high.

| # | Visual | Notes |
|---|--------|-------|
| 1 | **Generated image** | If an image-generation tool is available, generate the anchor (a Paris skyline, an elephant, a filled stadium) and place it. Prompt for a clean, on-brand style and pull the deck's palette into the prompt so it sits natively. |
| 2 | **Detailed vector / shape art** | Build a recognizable illustration from shapes — a real skyline silhouette (Eiffel Tower + varied rooflines), an animal silhouette, a stadium bowl — composed of many shapes, in the deck's colors, line weights, and flat-vs-shadowed style. **Not** one rectangle or a lone circle standing in for the thing. |
| 3 | **Native chart / sized primitives** | Bar/column charts, size-scaled circles or bars, a simple shaded map — on-theme and editable — when the point is quantitative rather than pictorial. |
| 4 | **Icon or glyph** | A landmark/person/object icon from the deck's set, when a full illustration isn't feasible. |
| 5 | **Typographic scale** | Last resort: carry the comparison with size contrast alone — hero number huge, anchor line beneath. |

Rungs 1–2 are the goal for a *pictorial* anchor (a place, an object, a creature);
rung 3 for a *quantitative* one (vs rivals, share of a whole). Even at rung 5 the
anchor line is still shown, so the number is never *naked* — just un-illustrated; the
comparison still lands, but reach for a real illustration first.

**Match the deck.** Whichever rung, sample colors, stroke weights, corner radius, and
shadow/flat style from the surrounding slides so the visual looks made *for this
deck*. Don't paste in a mismatched clip-art look. Don't describe an image you didn't
actually insert.

## 5. Layout blueprints

All blueprints: use a presentation-ready title that states the takeaway rather than
the technique; one idea per slide; body text left-aligned (centre only a single big
statement); detail moved to speaker notes; **no accent line under the title**.

**Scale Anchor** — hero number top-left in the accent color; anchor sentence
directly beneath at a clearly supporting size ("≈ the population of Paris"); the
skyline / landmark / map filling the right half or bleeding off the right edge.

**Competitive Benchmark** — the description in the title states the conclusion
(`Competitive Benchmark - We're the category leader`) — **but only when you have the
real comparison figures.** While rivals are still `[confirm figure]` placeholders,
use the frame (`Competitive Benchmark - How we compare on monthly actives`) and leave
their bars unsized; a verdict drawn over invented bars is a fabricated conclusion. Bar chart,
our bar in the accent color and every other bar in a single muted grey. Sort
descending. Data labels on, axis lines off, gridlines off.

**So-What Statement** — full-bleed dark background in the dominant color; the title
is the one dominant sentence, e.g. `Customers churn because they never got
started`. An optional support line may sit beneath at a clearly supporting size.
Nothing else.

**Big Stat + meaning** — the number as hero, its reference point immediately below in
the same visual block so the two read as one unit. Never the number alone.

**Before/After or vs Target** — two cards side by side, equal size; the "after" or
"target" card in the accent color, the other muted; one number and one short label
each; an arrow or delta between them.

**Analogy Visual** — the metaphor as a large simple diagram (funnel, iceberg, relay),
labelled with the deck's own terms; one line of text tying image to point.

**Pillars / Process / Grid** — only when the slide genuinely has ~3 points, a
sequence, or ~4 parallel items. Equal-weight blocks, one icon and ≤6 words each, the
detail in notes.

## 6. Alignment & balance

A better idea placed sloppily isn't better. Lay every slide on a grid.

**Snap to shared edges.** Pick a few guide lines — a left margin, a content-left
edge, a right margin, 2–3 columns — and put every element on one of them. Items that
are *nearly* aligned must be made *exactly* aligned:

- If several text lines or blocks start at roughly the same left position, give them
  the **identical** left (x) coordinate. Ragged, almost-aligned left edges are the
  single most common "sloppy slide" tell — the fix is one x-value for the whole group.
- A title, the body beneath it, and a footnote usually share one left edge.
- Rows of cards/columns share one **top** edge and one **height**; a row of numbers
  shares one baseline. Centered groups share one center line.

**Even, repeated spacing.** Choose one column gap and one row gap and reuse them —
equal gaps between peers read as deliberate. Don't mix a 0.3" gap here and 0.6" there.
Keep ≥0.4" clear of every slide edge.

**Balanced composition — fill the slide.** Distribute visual weight; never pile all
content in one half with the other blank:

- Two roughly equal blocks → two columns with a shared gutter.
- One hero + support → hero on one side, the visual (chart / skyline / icon grid) on
  the other, each occupying its half.
- A single statement or big number → optically centered, even breathing room top and
  bottom, not jammed under the title.
- Everything on the left with the right empty is a bug: move the visual there, widen
  the content, or center the whole block.

**Self-check before verify:** would horizontal guides touch the tops of things that
should line up, and vertical guides their left edges? Is either half conspicuously
empty? Fix before moving on.

**Emphasis & readability (hierarchy).** A balanced grid still fails if everything
shouts equally. Give each slide **one** focal point:

- **A single read-order.** The eye should land on the takeaway/hero first, then the
  support. Make the hero the largest thing and give it the most space; set supporting
  text markedly smaller and in a quieter tone.
- **One accent.** The accent color marks the one thing that matters (the hero number,
  the winning bar, the key word). Everything else is neutral/grey. Two accents = no
  accent.
- **Readability.** Text must remain readable at presentation distance. If content
  will not fit, cut words or move them to the notes rather than shrinking it into
  illegibility.
- **Contrast that holds** — dark text on light, light on dark; never light-grey text
  on a light card. Check it survives the deck's actual colors.

## 7. Speaker notes

The slide now carries one idea. Retained supporting context lives here — and the
notes are what the presenter actually reads, so **write** them rather than just
dumping into them.

Every generated slide's notes carry four things, in this order:

1. **The trimmed detail.** In **Keep the content**, useful content removed from the
   slide is moved rather than deleted; every source figure remains on the slide or
   in its notes. In **Rework the story**, supporting content may be omitted, but
   the notes should retain useful presenter context and the handoff must disclose
   every omission reported by the verifier.
2. **The anchor's provenance and exact figure.** Name where the comparison came from
   and what it rounds from, since the slide only ever shows the rounded form —
   *"Paris ≈ 2.1M (anchor-library population table, reviewed 2026-07)."* If the
   anchor came from the deck itself — last quarter, plan, another segment — say
   which slide. The presenter has to answer "says who?" without you in the room.
3. **One delivery line.** What to actually say over the slide, in the presenter's
   voice: *"We've added a Paris this year — that's the scale we're at now."* One
   sentence. The notes are a prompt, not a script.
4. **Any unresolved placeholder, spelled out.** *"[Competitor B — confirm figure] is
   still open — do not present these bars as real."* The chat handoff is long gone
   by the time they open the deck to rehearse, so the warning has to live on the
   slide it applies to.

**Example** — the Scale Anchor build from `worked-examples.md` §1:

```
2.3M monthly active users; 1.9M of them new in the last 12 months.
Anchor: Paris ≈ 2.1M (anchor-library population table, reviewed 2026-07);
the slide rounds this to "the population of Paris."
Say: "We've added a Paris this year — that's the scale we're at now."
```

**Don't restate the slide.** If the notes only repeat the hero number and the anchor
line, they've done nothing for the presenter.

## 8. Insertion and safety rules

- Insert the three alternatives as one ordered block at **source + 1..3**. Do not
  reorder anything else.
- **Leave the original slide untouched.** Replace it only on explicit request — the
  user wants the before/after comparison.
- In **Keep the content**, preserve every source number exactly — same digits,
  sign, currency, % and cadence — on the slide or in its notes. In **Rework the
  story**, a supporting number may be omitted, but any retained number follows the
  same exactness rule. `2.3M` never becomes `2,300,000` and `$5M` never becomes
  `5M`. A trailing zero or "million" spelled out reads the same and is fine. New
  anchor numbers are additions, never edits.
- In **Keep the content**, move cut text to the **speaker notes** of the new slide
  rather than deleting it. In **Rework the story**, disclose supporting text or
  figures that were combined or omitted. Write the rest of the notes per §7.
- Save to `$OUTPUT_DIR/output.pptx`, then run the step 6 checks with
  `$SKILLS_DIR/reimagine-this-slide/scripts/verify_slide.py`, passing
  `--expected-offset 1`, `2`, and `3` plus `--content-mode strict` or
  `--content-mode broad` for the three alternatives.

## 9. Rollback

If a built slide is wrong or the user rejects a set, delete **the slides you actually
created** — track their positions as you build rather than assuming *n+1*, since
insertion can land elsewhere. The source slide was never modified, so nothing else
needs undoing.

Two cases differ:

- **The three-slide set (the default):** on "show me alternatives," delete all three
  before building the next set so the deck doesn't accumulate throwaways; on "keep
  one," delete the other two. Say which you removed.
- **The user asked you to replace the source:** there's no separate slide to delete,
  so this is the one build in this skill that isn't trivially reversible. Confirm
  before replacing, and keep the original's text and figures to hand so you can put
  it back.

Then return to step 6 with the remaining directions — do not silently rebuild the
same one.
