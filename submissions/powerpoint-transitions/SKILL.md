---
name: powerpoint-transitions
description: "Create native PowerPoint transitions and cross-slide object animations. Use when asked to compare neighboring slides, animate matching pictures, shapes or text boxes moving, resizing or rotating together, add Morph, Push, Wipe or Fade, or reduce motion. Offers classic transitions only, matched objects only, or both."
---

# PowerPoint transitions

Make the audience's eye land on the right thing as the slide changes. Deliver a new editable `.pptx` when the host can read and return files; otherwise deliver an actionable transition plan. This is for movement **between** slides, not builds or entrance animations on a single slide.

## First: let the user choose

For each new deck task, **before comparing objects, planning effects, or editing**, ask this single-choice question and wait. Use a choice picker if the host offers one, otherwise ask in chat. If the user already explicitly chose one of the modes in this request, acknowledge it and proceed; do not ask twice.

> Which motion style do you want?
> 1. **Classic transitions only** — the original workflow: Fade, Push, Wipe, None, or a deliberately handpicked Morph. No automatic object comparison.
> 2. **Matched objects only** — compare adjacent slides and animate corresponding objects moving, resizing, or rotating. Leave transitions on other slide pairs as they are.
> 3. **Both** — use matched-object Morph where it explains a change, and classic transitions where there's no useful object match.

Keep that choice for the task, including revisions. Don't silently pick Both. If there is no way to collect a choice, offer the three options without editing. A request to explain or demonstrate the modes is not permission to change a supplied deck. An explicit reduced-motion constraint takes priority.

## 1. Read the story before choosing motion

- Start with the actual deck, or an ordered outline if no file is available. If neither is supplied, ask for one. For a new deck, create the slides with the host's normal presentation tools first.
- Identify the moment worth moving: what stays the same, what changes, and where the viewer's attention should land. Use the existing slide order, including hidden slides in numbering. Be careful with custom shows, branches, or hyperlinks that skip the previous slide.
- Default to a speaker advancing on click on new slides. Preserve any existing rehearsal/kiosk timings on edits. Do not add sounds, change the layout, duplicate slides or reorder content just to fit an effect without permission.

## 2. Choose a motion pattern

| Relationship | Direction for the editor | Starting duration |
|---|---|---|
| An overview becomes one detail | **Morph / Objects**. Pick one recognizable tile, icon, or image on both slides. In the detail view it grows and moves to its final position. Keep a second detail from competing for attention. | 0.8 s |
| Before becomes after in the same frame | **Wipe** across the change. Keep the two layouts registered so the boundary reveals the difference. If the eye must track the same object changing position, use Morph instead. | 0.45 s |
| One process stage gives way to the next | **Push** along one axis. Follow the actual reading direction of the sequence; reverse only to signal a return. | 0.5 s |
| A new chapter or conclusion starts | **Fade** rather than manufacturing a spatial relationship. Hold the final slide still. | 0.35 s |
| Dense reading, unrelated layouts or a motion-sensitive audience | **None**. If the user asks for gentle rather than zero motion, use only a brief Fade. Never make motion the only way to understand a change. | None / 0.25 s |

Use one motion pattern for a recurring relationship, not a different effect on every slide. Start slide 1 still. For a keynote, spend the boldest move on one reveal; for an executive briefing, suppress moves that don't explain something.

**Three moves to try when authoring slide pairs:**

- **Map dive.** The overview contains a product screenshot with a coral pin. The next slide shows a closer crop; place the same pin over the same feature. Match the pins as `!!focus` and Morph for 0.8 s. The screenshot can change instantly; the pin gives the viewer a point to follow.
- **Poster to nameplate.** Start a chapter with a large wordmark. On the first content slide, move a smaller copy into the corner normally used for the section label. Match the two as `!!chapter` and Morph for 0.7 s. Leave the body text still on subsequent slides.
- **Comparison curtain.** Duplicate a diagram, change only its final state, and leave the scale, labels and frame exactly registered. Wipe across the improvement in 0.45 s. Do not wipe between charts with different axes: that would imply the values can be compared on the same scale.

## 3. Compare objects (Matched objects or Both only)

In an editable deck, start with a **read-only** comparison. Paths below assume the skill folder is the working directory. `--plan` writes only eligible matches to a **new** JSON file; the printed report also explains uncertain pairs and detected movement.

```text
python scripts/transitions.py compare input.pptx --plan matched.json
```

- Look for continuity, not just similarity: a product photo moves from the sidebar to the hero position while its caption moves underneath it; or two labeled process cards trade places. Each pair gets its own unique `!!` name; all selected pairs share **one** native Morph on that slide advance.
- Review `pairs` for the requested slide range. The matcher uses unique shared bindings, distinctive names, identical embedded image data, or matching text. It checks for actual position, size or rotation changes. Objects that only look alike (same preset shape and fill) go to `review`, not the plan. **Skip uncertain pairs or ask the user to identify them; never match by slide order or proximity alone.**
- Scope: top-level shapes, text boxes and embedded pictures with explicit geometry. It skips groups, placeholders, linked pictures, hidden slides, and unsupported transitions. It doesn't recognize an object *inside* a flattened screenshot, synthesize motion paths, or guarantee that other slide elements remain still: PowerPoint controls their normal Morph/fade behavior.
- Remove speculative or distracting pairs from `anchors`. If adding a user-confirmed pair, use original Selection Pane names in `from`/`to`, and assign a unique `!!name`. Use the same `!!name` along a chain; never bind one object to two. The editor does not move or redraw objects to manufacture motion.
- **Matched objects only:** apply only `matched.json` entries under `--mode objects`; don't add a Fade, Push, Wipe, or even a cleanup cut elsewhere. If nothing qualifies, say so and leave the deck untouched. **Both:** keep selected Morph entries, add handpicked classic entries only at other destinations, and use `--mode both`. A destination can have one transition, not a simultaneous Morph and Push.
- If Python isn't available, compare slide pairs visually and in the Selection Pane using the same evidence and rules. Without access to the actual slides or object metadata, describe *possible* matches as a plan only; do not claim detection.

## 4. Apply on the destination slide

**File + Python available:** use [the portable editor](./scripts/transitions.py) with Python 3.9+ (standard library; no downloads, Office install, or credentials). Paths below assume the skill folder is the working directory. Work only on an authorized local copy; obtain cloud files through the host's approved file tools.

```text
python scripts/transitions.py inspect input.pptx
python scripts/transitions.py inspect input.pptx --slide 2
python scripts/transitions.py apply input.pptx motion.json output-motion.pptx --mode classic
python scripts/transitions.py inspect output-motion.pptx
```

For matched objects only: `python scripts/transitions.py apply input.pptx matched.json output-motion.pptx --mode objects`. For Both, use a merged plan and `--mode both`. These commands never modify the input.

Write a JSON list with **1-based destination slide numbers in presentation order**; omit slides that should stay untouched. Example (replace the sample slide numbers and names after inspecting the actual deck):

```json
[
  {"slide":2,"effect":"morph","ms":800,"anchor":{"from":"Overview marker","to":"Detail marker","name":"!!signal"}},
  {"slide":3,"effect":"push","direction":"left","ms":500},
  {"slide":4,"effect":"wipe","direction":"right","ms":450},
  {"slide":5,"effect":"fade","ms":350},
  {"slide":6,"effect":"none"}
]
```

- `from` is a shape name on the preceding slide, `to` on the destination. Use existing, distinctively positioned or sized shapes of the same kind. The editor assigns the same unique `!!name` to both on the copy. If the shapes already share a forced name, use `"anchor":"!!signal"`. The helper does not invent geometry or add objects. On consecutive Morph moves, reference the already assigned name on the shared slide.
- `direction` describes **travel**, not the edge where it starts: `left` means movement toward the left (PowerPoint's *From Right*). `left`, `right`, `up`, `down` are supported for Push and Wipe. `ms` is the transition's duration, **not** time before advancing.
- Use a **new output filename**. Only selected transitions and requested Morph shape names change; existing click/after settings survive. Unsupported files or complex targeted transitions (e.g. with sound) produce an error, not a partial edit. Do not bypass protection; offer the native or plan path instead.

**PowerPoint controls available, but not Python:** save a copy. Select the destination thumbnail, then **Transitions > effect > Effect Options > Duration**. For Morph, use **Objects**. In the **Selection Pane** give the corresponding shape on each slide the same unique name beginning with `!!` (e.g. `!!signal`). If authoring a new pair, duplicate the first slide, then move or resize its shape on the duplicate. For reduced motion use **Transitions > None**. Don't select **Apply To All** unless specifically requested.

**No file writer:** return `From > To | audience cue | effect + option | seconds | object/prep | reduced-motion alternative`. Give the exact PowerPoint clicks above. If you have only an outline, identify any assumed object names. Say **plan only; no deck was edited**. Do not substitute CSS, GIFs, or video for native transitions.

## 5. Verify and deliver

1. Reopen or inspect the **output**, not the input. Verify the destination ordinals, duration, direction, Morph pair, advance settings, and unaffected slides. Check both endpoints still make sense as static slides.
2. In PowerPoint Slide Show, start on the **preceding** slide and advance. Did the correct object move, and did attention land on the intended detail? A thumbnail, PDF, or XML inspection cannot verify playback. If you couldn't preview, state what you did verify and give the user that playback check.
3. Return a link to the new deck, the chosen mode and a short list of changed pairs. For matched objects, name the objects and describe their moves; distinguish confirmed matches from anything left out. Flag fades/cuts used in place of a planned Morph. The editor embeds a Fade fallback for viewers that don't understand Morph; actual playback depends on the viewer.
