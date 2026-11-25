# Worked examples

Scenarios showing input → actions → result, including the edge cases that trip this
skill up. Examples 1–6 are the **text / whole-slide** branch (menus A & D); examples
7–8 show the **chart** and **image** branches (menus B & C). The first is canonical;
the rest are worth reading before you improvise.

---

## 1. The naked stat (canonical)

**Source slide:** Title "Growth." One line: "Our app has 2.3M monthly active users —
1.9M of them new in the last 12 months." Speaker notes: "This is the headline for
the board — we want them to feel the scale."

**Step 1–2 — point and gap.** The point is *scale*. The gap is a missing reference
point: 2.3M is a fact with nothing to compare against.

**Step 3 — anchor test.** Paris sits in the library's 2–3M population band, is
familiar to this board, and is an equivalent rather than a superior. The rate option
uses the trailing-12-month *flow* (1.9M new users), not the 2.3M monthly-active
count — MAU is a population, not a flow, so converting it to "users per second"
would state something the data never said.

**Step 3 (cont.) — the 3 directions** (all pass the anchor test, all distinct):
- **A · Scale Anchor** — "2.3M users ≈ the population of Paris," hero number over a
  Paris skyline. Feels big.
- **B · Competitive Benchmark** — bar chart: us 2.3M vs rivals. Shows exactly where
  we stand — needs their real figures before it can claim a winner.
- **C · Rate** — 1.9M new in the last 12 months ≈ "a new user every 17 seconds," a
  bold statement slide. Feels alive.

**Step 4 — build all 3 automatically** (no prompt). Preserve the source and construct
A, B, C at source+1..+3 using its theme/master, titled `2.3M users is about the
population of Paris`, `How we compare on monthly actives`, and
`A new user every 17 seconds`, laid out on a grid (aligned edges, even gaps,
filled composition per `build-recipes.md` §5). Original untouched. In **B**, our 2.3M is in the theme
accent; rival figures are inserted as `[Competitor B — confirm figure]`, the rival
bars stay unsized, and the title states the frame — `How we compare on monthly
actives`, **not** `We're the category leader` (that verdict isn't evidenced until
the user supplies the numbers).

Speaker notes for B written per `build-recipes.md` §6 — trimmed detail, anchor
provenance, a delivery line, and the open placeholder carried over:

```
2.3M monthly active users; 1.9M of them new in the last 12 months.
Benchmark: our 2.3M is from the source slide. Rival bars are NOT real —
[Competitor B — confirm figure] is still open; do not present them as data.
Say: "Here's where we sit against the field — I'll fill in their numbers
before Thursday."
```

**Step 5 — polish first, then verify each built slide.** *Polish sweep (automatic, no
questions):* on the Competitive Benchmark slide the legend duplicated its direct bar labels and the axis
title "Users (M)" echoed the slide title — both cut; the bar labels are snapped to one
baseline. Nothing was reordered or rewritten (that would be redesign). Then run the
checks rather than eyeballing them (shown here for the Competitive Benchmark slide at slide 5; do the same for
A and C):

```
$ python3 "$SKILLS_DIR/reimagine-this-slide/scripts/verify_slide.py" \
      --deck "$OUTPUT_DIR/output.pptx" --source 4 --built 5 \
      --expected-offset 1
REIMAGINE_THIS_SLIDE_VERIFY_OK=1
{
  "ok": true,
  "deck": "/Users/me/decks/output.pptx",
  "source_slide": 4,
  "built_slide": 5,
  "checks": {
    "chart_data_readable": true,
    "numbers_exact": true,
    "no_placeholders": false,
    "position_matches_expected_offset": true,
    "no_accent_line_under_title": true,
    "fonts_match_deck": true,
    "effects_match_deck": true,
    "title_present": true
  },
  "not_checked": [
    "source slide unmodified (needs a pre-build baseline)",
    "theme colors (only fonts are compared)",
    "numbers inside pictures or SmartArt",
    "most chart number formats (only explicit percentage data labels are rendered)"
  ],
  "source_numbers": [
    "2.3M",
    "1.9M",
    "12"
  ],
  "errors": [],
  "warnings": [
    "Unresolved placeholder(s): [Competitor B - confirm figure]. Not a defect, but name them explicitly in your handoff so they are never presented as real figures."
  ]
}
$ echo $?
0
```

Exit 0 with one warning: the slide is sound, but the placeholder must be surfaced.
Note `no_placeholders: false` alongside `"ok": true` — of the seven reported checks it
is the sole advisory; the other six are required and any of them failing blocks.
Four things worth knowing:

- **`--built` is required**, deliberately. Letting it default to source+1 would mean
  the script assumed the very thing it is supposed to check.
- **`"12"` is in `source_numbers`** because "the last 12 months" really is a figure
  on the source slide. It's accounted for in the built slide's notes, so it passes.
- **Had the hero drifted to `2.4M`**, `numbers_exact` would be `false`, exit code 1 —
  a hard stop. That holds even if `2.3M` still sits in the speaker notes: a source
  figure surviving only in the notes while a near-miss shows on the slide face is
  reported as an altered headline, not a pass.
- **Had it been rewritten as `2,300,000`**, that's an error too — same value, but the
  audience reads something different. Re-run with `--allow-reformat` only if the user
  actually asked for the new formatting.

Read `not_checked` as well: the script never proves the source slide is unmodified,
never compares theme colors, can't read numbers baked into a picture, doesn't inspect
how a chart formats its labels, and — importantly here — can't judge **alignment or
balance**. Those stay yours: eyeball each slide for ragged edges and lopsided
composition before handing back.

**Step 6 — summarize + offer alternatives.** "Built 3 versions after your Growth
slide — A: '≈ the population of Paris' over a skyline; B: a benchmark bar vs rivals
(their figures flagged for you to confirm); C: 'a new user every 17 seconds.' Polish
pass tidied B — dropped a redundant legend and axis title and aligned the bar labels.
Want me to keep one and delete the others, refine one, or show 3 alternative ideas?"

---

## 2. The wall of bullets (no number to anchor)

**Source slide:** Title "Why customers churn." Seven bullets: "Onboarding is too
long · Users don't reach first value fast enough · Support response times slip in
week 2 · Pricing confusion at renewal · Feature discovery is poor · Competitors ship
faster · No proactive outreach."

**Step 1–2 — point and gap.** Seven bullets, no hierarchy, no number, no takeaway.
Reading the notes: "The real issue is they never get to first value." That's the
point — the other six are symptoms.

**Step 3 — anchor the *idea*, not a figure.** No stat exists, so reach for the
analogy bank (`anchor-library.md` §7): progressive loss at each stage → a funnel or
leaky bucket.

**Step 4 — build 3 directions directly (no chat pitch):**
- **A · Analogy Visual** — a leaky bucket: seven small leaks, one big one labelled
  "never reached first value." Feels like an obvious fix.
- **B · So-What Statement** — full-bleed title: `Customers don't churn because
  we're missing features. They churn because they never got started.`
  Feels like a verdict.
- **C · Pillars** — collapse 7 bullets into 3 causes (Activation · Support · Pricing),
  one icon each, detail in notes. Feels organised.

All three are built as slides after the source. **B**, for instance, is a dark
full-bleed slide, one sentence at 54 pt, a small support line, and all seven original
bullets preserved in the speaker notes — nothing was deleted, it moved. Each is laid
out on the grid (the pillars in C share one top edge, equal gaps, and span the slide
width rather than hugging the left).

**Why this one matters:** "a wall of bullets" is a headline trigger, and the instinct
to hunt for a number will fail here. Anchor the idea instead.

---

## 3. Two rounds of alternatives (hitting the stopping condition)

**Round 1 — build 3.** Scale Anchor, Competitive Benchmark, Rate — built as slides.
The user reviews and says **"none of these — show me alternatives."** (3 built.)

**Round 2 — fresh anchor types, never repeats.** Build Money Equivalent, Before/After,
Analogy. **User asks for alternatives again.** (6 built.)

**Round 3 — the last set.** Two rounds of alternatives have been spent, so this is the
third and final set: a world-population share, a stadium-fill visual, a So-What
Statement. **User rejects this set too.** (9 built.)

**Round 4 — do NOT build a fourth set.** Nine directions have failed, which means the
*diagnosis* is wrong, not the execution:

> "I've built 9 directions and none landed, so I think I'm anchoring the wrong thing.
> What's the one takeaway you want this slide to leave the audience with — and who's
> the audience?"

**User:** "It's for the engineering team, and the point isn't growth — it's that the
infrastructure won't survive it."

**Restart at step 1** with the corrected point and reset the count. The next set is
about capacity headroom, not scale, and it lands.

**Contrast — this is *not* a new round:** if the user says "too corporate, no sports
references," that's a refinement. Apply the constraint, rebuild, and don't count it.

*(Housekeeping: clear the rejected slides as you go — delete a round's three slides
when the user asks for alternatives. Nine directions are attempted; nine throwaway
slides never coexist.)*

---

## 4. The slide that's already good

**Source slide:** "Support tickets fell 38% after the redesign — from 1,240/month to
770/month." A clean before/after chart, theme-consistent.

**Actions:** Step 1 finds a clear point. Step 2 finds no gap — the number already has
its reference point (the before figure), and the visual already carries it.

**Result — decline, don't manufacture work:**

> "Honestly, this one already lands — you've got the change, the baseline, and a
> chart that shows it. The only thing I'd tighten is the title: 'Support tickets fell
> 38%' states the fact; 'The redesign cut support load by a third' states the
> so-what. Want me to make just that change, or leave it?"

Proposing three redesigns of a working slide is noise, not help.

---

## 5. Out of scope — the chart restyle

**User:** "This chart looks ugly, can you fix the colors?"

**Actions:** This is a restyle of an existing chart, which the description excludes.
Decline the restyle, but offer the adjacent thing this skill *is* for:

> "That's a restyle rather than a re-story, so it is out of scope here. What I can
> do is give the chart a point — right now the title is
> 'Revenue by region,' which is a label, not a takeaway. Want me to look at that?"

**Note the boundary:** this skill won't restyle a chart that already exists, but it
*will* build a new chart when Competitive Benchmark is the chosen direction. Creating
is in scope; restyling isn't.

---

## 6. Degraded visual — only when the rich options truly aren't available

**Situation:** Same Growth slide as example 1 — "2.3M monthly active users — 1.9M of
them new in the last 12 months." The Scale Anchor direction — one of the 3 being
built — is "2.3M ≈ the population of Paris." **Reach for a rich visual first:** if an
image tool exists, generate a Paris skyline; otherwise draw a detailed skyline
silhouette in shapes. Only if *neither* is possible do you degrade.

**Actions:** Walk the visual chain (`build-recipes.md` §3) top-down and take the
highest rung actually available:

- *Rung 1, generated image* — no image-generation tool in this environment. Skip.
- *Rung 2, detailed vector silhouette* — attempted, but this constrained run can't
  compose a recognisable skyline from shapes. (In a normal run this is the target —
  don't skip it lightly.)
- *Rung 3, native chart/sized primitives* — a bar chart of a single number isn't a
  comparison. Skip.
- *Rung 4, icon/glyph* — this deck has no icon set or landmark glyph.
- *Rung 5, typographic scale* — available. Use it.

The slide is still built natively at source+1. The missing picture is not allowed to
cancel the anchor — but note how far down the chain you had to go, and prefer a
richer rung whenever you can actually produce it.

**Result:** a built slide carrying the comparison with type alone —

> `2.3M` as the hero in the theme accent, left-aligned, with
> "≈ the population of Paris" directly beneath at a clearly supporting size. The notes
> carry the trimmed detail, the anchor's provenance, and a delivery line, so **every
> source figure survives** and step 5 passes:
>
> ```
> 2.3M monthly active users; 1.9M of them new in the last 12 months.
> Anchor: Paris ≈ 2.1M (anchor-library population table, reviewed 2026-07);
> the slide rounds this to "the population of Paris."
> Say: "We've added a Paris this year — that's the scale we're at now."
> ```

And the handoff says so plainly:

> "Built it after your Growth slide. I couldn't get a Paris skyline, so this version
> carries the comparison with type instead — it still lands. Want me to try it as a
> bar chart against rivals instead?"

**The rule this demonstrates:** degrade the *visual*, never the *point*. A hero
number with its reference point set in type still lands. A naked number — the
comparison dropped because the picture wasn't available — is the one outcome this
skill must not produce.

---

## 7. A chart is selected (menu B)

**Selected:** a 6-slice **pie chart** of revenue by region. **Point:** one region
dominates. **Diagnosis:** a pie makes six slices hard to rank — wrong form for a
"which is biggest" job.

**3 directions built:**
- **A · Sorted bar** — the six regions as a horizontal bar, largest on top. Ranking
  is instant. (menu B1)
- **B · Big stat + small bar** — hero "48% — West" with a slim supporting bar for the
  rest. Says the point outright. (menu B2)
- **C · Map** — a region map shaded by share. Geographic and memorable. (menu B2)

**All three built** as new slides after the source. Example — **A**: a native
sorted horizontal bar, same figures, title `The West is carrying us`
(the data supports it, so the verdict is allowed), bars sharing one left baseline
and even row gaps. Original pie untouched. Verify each: shares unchanged ✓,
positioned after the source ✓. Then summarize and offer alternatives.

**Rule:** match the chart form to the data's job; a new chart is in scope, while a
pure recolor of the existing one is not.

## 8. An image is selected (menu C)

**Selected:** a stock photo of a handshake on a "Partnerships grew 3×" slide.
**Diagnosis:** it is decorative because it adds no information; the point is the 3×
growth.

**3 directions built:**
- **A · Pictograph** — a row of partner icons, one highlighted set showing the 3×.
  (menu C → B2)
- **B · Big stat + icon** — "3×" as the hero with a small partnership icon. (menu C)
- **C · Before/after cards** — "Last year 40 → Now 120." Shows the jump. (menu A2)

**All three built** as new slides; the photo slide is left intact until the
user chooses. Example — **B**: title `Partnerships tripled`, with
"3×" as a themed hero and a supporting icon, optically centered. No numbers to
fabricate; "3×" preserved. Then offer to keep one (and delete the photo slide) or
show alternatives.

**Rule:** replace a decorative image with a visual that carries the point — but if
the image is *informational* (a screenshot, a real product photo), keep it and offer
a takeaway caption instead.
