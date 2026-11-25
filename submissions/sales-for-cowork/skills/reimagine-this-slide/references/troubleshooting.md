# Troubleshooting

Failure modes, their causes, and what to do. Rollback for the build step is in
`build-recipes.md` §8.

---

## Reading the slide

| Situation | Cause | Action |
|-----------|-------|--------|
| The slide's point is genuinely ambiguous | Several competing takeaways, or a title like "Q3 Update" | Ask before proposing: "What's the one thing you want them to remember?" Don't build against a guessed premise. |
| The slide is a wall of bullets with no number | Qualitative content | Anchor the *idea*, not a figure — use the analogy bank, or a Before/After if the bullets describe a change. Cut aggressively and preserve useful detail in notes. |
| The bullets say one thing, the speaker notes say another | The real argument lives in the notes | Trust the notes — that's the point the presenter actually makes. Say which you used. |
| The slide has 12 numbers and no hero | A data dump | Ask which number is the point, or pick the one the title refers to and state your choice. Don't anchor all of them. |
| The slide is already good | It has a clear point and a reference | Say so. Offer one small sharpening or decline: "This one already lands — want me to leave it?" Don't manufacture work. |
| The slide is a chart that just needs restyling | Out of scope | Say: "That's a restyle rather than a re-story, so it is out of scope here. I can add context around it if you want." |

## Anchoring

| Situation | Cause | Action |
|-----------|-------|--------|
| No anchor feels right | The metric is domain-specific (bps, ARR churn, p99 latency) | Anchor to the deck's own history or target — last quarter, plan, or the other segments. An internal benchmark always beats a strained external one. |
| You need a competitor's figure | External fact you can't verify | Insert `[Competitor B — confirm figure]`. **Never state one from memory.** Chart the shape with our bar real and rivals placeholdered. |
| The comparison is close but not exact | Rounding | Fine — that's expected. Frame with "≈", "about," or "roughly" and round to something memorable. Exactness is required of the *source* numbers, not the anchor. |
| The **scale** anchor is bigger than the stat | Wrong direction (this applies to scale anchors only — for a benchmark, a bigger rival or target is the point) | Flip it or drop it. "2.3M — about a quarter of London" is weak; find an equivalent, not a superior. |
| The audience won't know the reference | Wrong region or domain | Localize (see `anchor-library.md`). If unsure who the audience is, ask — it's one question and it changes every option. |

## Presenting options

| Situation | Cause | Action |
|-----------|-------|--------|
| The user replies with a critique instead of choosing ("too corporate") | They're refining, not asking for a new set | Apply the constraint and rebuild. **Does not count against the alternatives limit.** |
| The user asks to combine two options | Both anchors work | Build the hybrid — keep one anchor dominant so the slide still has one idea. |
| Three sets rejected and still nothing lands | The diagnosis in step 1 is wrong, not the execution | **Stop. Do not build a 4th set.** Ask for the takeaway and the audience, then restart at step 1 and reset the count. |
| The user says "an idea" in the singular | Conversational phrasing, not a quantity override | Build the default three unless the user explicitly asks for exactly one output. |

## Building

| Situation | Cause | Action |
|-----------|-------|--------|
| You can't insert the complete three-slide block where required | The deck is protected, or the layout won't take the content | Roll back every slide created in that attempt so the source remains intact. Say plainly that the atomic three-slide build could not be completed, name the cause, and do not describe or deliver a partial set. |
| Theme colors/fonts unreadable | Corrupt or unusual master | Use the source slide's own fonts and dominant fill; tell the user you approximated. |
| Anchor visual looks basic (one flat shape for "Paris") | Reached for the lowest-effort visual | Build a *detailed* silhouette/scene (§3 rung 2) or generate an image (rung 1), in the deck's style. A lone rectangle/circle isn't an illustration. |
| No rich visual possible for the anchor | No image tool and can't compose a detailed silhouette | Degrade down §3: generated image → detailed vector → native chart → icon → typographic scale. Go as high as you can; **never ship a naked number**. |
| A content edit needs implementation | The slide must be changed portably | Use the installed `python-pptx`, save to `$OUTPUT_DIR/output.pptx`, and do not extract or rebuild the OOXML package. |
| The deck is 4:3, not 16:9 | Older template | Match the deck's dimensions. Don't insert a 16:9 slide into a 4:3 deck. |

## Verifying

| Situation | Cause | Action |
|-----------|-------|--------|
| `verify_slide.py` reports a **changed** number | A source figure was altered or mis-rounded | **Hard stop.** Fix it to match the source exactly, re-run, and don't hand the slide over until it passes. |
| `verify_slide.py` reports a **missing** number | The figure is on neither the built slide nor its speaker notes — the script already searched both | **Not "usually fine."** Restore it to the slide or its notes; there is no flag that waves this through, because the skill trims text into the notes rather than deleting it. The one benign cause is a figure the extractor can't reach — inside a picture or SmartArt — so check that by eye before treating it as a defect. |
| `verify_slide.py` reports a **reformatted** number | The value matches but the token changed — `2,300,000` where the source said `2.3M` | The number is right; what the audience reads is not. Restore the source's formatting unless the user asked for the change. |
| `verify_slide.py` reports **fonts don't match the deck** | The new slide used a font that appears nowhere else | Restyle it to the deck's heading and body typefaces. This is a required check, so it blocks. |
| The title check **fails** | The title placeholder is empty or missing | Put the slide's presentation-ready takeaway in its actual title placeholder. A matching ordinary textbox does not satisfy this required check. |
| An unresolved `[… confirm …]` placeholder remains | Expected — you couldn't verify an external fact | Not a defect, but **name it in the handoff**: "Ready — confirm Competitor B's figure before you present." Never let it ship silently. |
| The accent-line check **fails** | A thin rule was drawn under the title | Remove it — this is a required check, so it blocks. Use whitespace or a color block instead. |
| `verify_slide.py` exits 2 | Bad path, unreadable deck, or a missing dependency — the message says which | Fix the input if you can. If you genuinely can't run it, read the built slide and its notes back yourself and compare every figure on digits, sign, currency, % and cadence. Verification is never optional. |
