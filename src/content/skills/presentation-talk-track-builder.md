---
name: Presentation Talk Track Builder
description: "Writes natural, first-person spoken presenter scripts for the slides in a deck. Treats existing speaker notes as authoritative when they contradict slide text. Calibrates length to a target duration and speaking pace and returns a timing table. Never modifies visible slide content."
agentDescription: "Writes natural, first-person spoken presenter scripts (talk tracks) for the\nslides in a PowerPoint deck, from slide images, or from pasted slide text.\nTreats existing speaker notes as AUTHORITATIVE when they contradict slide\ntext. Produces one spoken script per slide with delivery cues, calibrated to\na target duration and speaking pace, plus a timing table. Use when the user\nsays \"write a script for these slides\", \"I'm presenting slides X-Y, what\nshould I say\", \"create a presenter script\", \"turn my speaker notes into a\ntalk track\", or \"make a 6-minute script for these slides\". Do NOT use to\ncreate or edit the visible content of slides, to summarize a recorded\nmeeting or transcript, or for general document writing.\n"
platforms: [Cowork, Copilot Studio, Scout]
tags: [presentations, speaker-notes, powerpoint, writing, productivity]
author: Jagmeet Chabra
authorUrl: "https://github.com/jchha001"
authorGithub: adilei
version: 1.0.0
createdAt: 2026-07-16
updatedAt: 2026-07-17
bundle: bundles/presentation-talk-track-builder.zip
---
## Overview

This skill turns slides into a spoken talk track. For each requested slide it
writes a first-person script the presenter can read aloud, grounded in the
slide's content and — above all — its **speaker notes**. It calibrates the
script length to a target time and speaking pace and returns a timing table
so the presenter knows whether they will land on time.

**Core rule:** the speaker notes are the source of truth. When notes and
slide text disagree, the script follows the notes and silently drops the
contradicted slide text. This is what the author intended to say.

Works across Scout, Copilot Studio, and Cowork. The user can attach a
`.pptx`, provide slide images, paste slide text, or provide an outline.

## When to Use

- "I'm presenting slides 8-11, write a script for each so I can present them."
- "Turn my speaker notes into what I should actually say."
- "Make a ~6-minute talk track for these four slides; I speak fast."
- "Write presenter narration for this deck / these slide images."
- "Give me a word-for-word script with pauses and a handoff to the next
  speaker."

## When NOT to Use

- Creating, designing, or editing the visible content of the slides
  themselves.
- Summarizing a recorded meeting, call, or transcript.
- Writing a standalone document, memo, or article.
- A quick one-line answer that isn't a spoken script — answer inline.

## Quick Start

```
User: "I'm presenting slides 8-11, write a script for each. If the notes
       contradict the slides, follow the notes. Target ~6 minutes, business
       audience."
1. Capture inputs — audience & goals, slide content, optional supporting
   context.
2. Extract BOTH slide text AND speaker notes for the requested slides.
3. Reconcile: where notes contradict slides, follow the notes.
4. Calibrate: target minutes × pace (words/min) = word budget; split by
   slide.
5. Write a first-person script per slide with delivery cues + a handoff line.
6. Return the scripts + a per-slide timing table (words → spoken minutes).
7. Offer to save as speaker notes back into a copy of the deck, or as a doc.
```

## Core Instructions

### Step 0 — Capture audience & goals (required)
Before writing anything, capture:
- **Audience**: who is in the room (or on the call)? Role, seniority,
  technical depth, familiarity with the topic.
- **Event context**: keynote, internal review, customer meeting, training,
  panel, webinar.
- **Presenter goal**: what should the audience *understand*, *decide*, or
  *do* after the presentation?
- **Tone**: formal, conversational, energetic, deliberate.
- **Target duration** and **speaking pace** (see Step 4).

If the user hasn't provided these, ask once. If they decline, use the
defaults below and label them as assumptions in the output:
- Audience: general business audience.
- Tone: clear, confident, conversational.
- Goal: help the audience understand the deck's main message and next step.

### Step 1 — Locate the slides and any supporting context
- If a `.pptx`/`.pptm` is attached or on disk, use it. Check the user's
  likely input folders first (Downloads, current workspace) even when the
  user does not name a path.
- If only slide **images** are provided, work from what's visible and tell
  the user there were no speaker notes to follow.
- If only pasted text or an outline is provided, use that directly.
- Confirm exactly which slide numbers to cover. If the user did not name
  specific slides, cover the whole deck.
- Ask the user for **optional supporting context** the model can weave into
  the narration (but not into the slides themselves): a product one-pager,
  a prior version of the talk, a customer brief, an FAQ, source links, or
  presenter background notes. This is especially useful when the existing
  speaker notes are thin or missing.

### Step 2 — Extract slide text AND speaker notes (both matter)
- Slide text and existing speaker notes can be extracted with the bundled
  helper:
  ```
  python scripts/pptx_talk_track.py extract <deck>.pptx <slides>.json
  ```
  The output JSON contains `title`, `visibleText`, and `existingNotes` per
  slide. Both fields matter.
- If you have python-pptx available you can also use
  `slide.notes_slide.notes_text_frame.text` to read notes.
- Map notes to the correct slide numbers.

### Step 3 — Reconcile notes vs. slides (notes win)
- Read both. Where the notes state something different from the slide (a
  different figure, name, framing, date, or emphasis), write the script to
  match the **notes** and drop the contradicted slide text.
- Where notes add context the slide omits, include it. Where notes are
  sparse, lean on the slide content and any supporting context to fill the
  spoken narrative — never invent.
- Note any contradiction you resolved in a one-line aside after the
  scripts, so the presenter knows why the script diverges from what's on
  screen.

### Step 4 — Calibrate timing to the target
- Ask for (or infer) two things: target duration and speaking pace. If the
  user says they "speak fast", use a brisk pace; otherwise default to
  average.
- Pace reference (words per minute):
  | Pace | WPM | Use when |
  |------|-----|----------|
  | Deliberate | 110-130 | Technical/dense content, non-native audience |
  | Average | 130-150 | Default |
  | Brisk / "I speak fast" | 165-185 | User says they rush or speak quickly |
- Word budget = target minutes × chosen WPM. Divide across slides by
  weight (slides with denser notes get more words). Compute totals and
  per-slide times with a code tool — never estimate arithmetic by hand.
- Presenters speed up live, so aim the *written* script slightly LONG of
  the target (e.g. write to ~6:15 for a 6:00 goal) and add `[pause]` cues,
  which both reinforce key points and naturally slow a fast speaker.

### Step 5 — Write the script (spoken, first person)
- One clearly-headed section per slide: `## Slide N — <short title>`.
- Natural spoken language, first person ("Let me show you…", "Here's why
  this matters…"). Contractions on. Short sentences. No bulleted
  fragments — full spoken prose.
- Put delivery cues in italics or brackets: *[pause]*, *(gesture to the
  diagram)*, *(click to reveal)*, *(hand off)*.
- Open each slide with a one-line bridge from the previous slide; close
  the last covered slide with a handoff line to the next presenter or to
  Q&A if relevant.
- Mirror the deck's terminology and the user's domain voice.
- Tailor the depth and framing to the audience captured in Step 0.

### Step 6 — Deliver with a timing table
- After the scripts, show a table: Slide | approx. words | spoken time,
  with a total and the estimated overall minutes at the chosen pace.
- Call out the easiest lines to cut if running long, and offer to tighten
  any slide to a specific per-slide time.

### Step 7 — Offer to save the output
- Offer to save the scripts back into a copy of the deck as speaker notes,
  using:
  ```
  python scripts/pptx_talk_track.py apply <deck>.pptx <notes>.json <output>.pptx
  ```
  The helper writes speaker notes only. It never changes visible slide
  content, order, formatting, images, charts, or animations.
- Alternatively, offer to save as a Word document for presenter notes.
- Only save a file when the user asks for one.

## Output

- Markdown by default (inline), one section per slide, in slide order.
- First-person spoken prose with italic delivery cues; a handoff line
  where relevant.
- A closing timing table (words + spoken minutes per slide, plus total)
  and a one-line note of any note-vs-slide contradiction resolved.
- Tone matches the deck; length matches the time budget.

See `references/tone-examples.md` for target voice samples.

## Guardrails

- **Notes are authoritative.** When speaker notes contradict slide text,
  follow the notes and drop the contradicted slide content — this is the
  whole point of the skill.
- **Never modify visible slide content.** Slide text, order, layouts,
  images, charts, and animations must stay unchanged. If notes are written
  back to a `.pptx`, only speaker notes in a copied file are updated.
- **Never fabricate facts.** Do not invent figures, names, dates, or
  quotes that aren't in the slides, notes, or supporting context. Mark
  genuine gaps as `[confirm: …]` rather than guessing.
- **Confidentiality and sensitivity.** If slides or notes carry a
  confidentiality label or sensitivity marking (for example
  "Confidential", "Internal Only", "Restricted", or an enterprise
  information-protection label), or contain unreleased figures,
  customer or partner identifiers, or names that aren't public yet,
  flag them and confirm with the user before including that content in
  the spoken script. Never add PII or customer identifiers the source
  material doesn't already contain.
- **Compute timings with code**, not by hand; state the pace assumption
  so the presenter can recalibrate.
- **Cover exactly the requested slides** — no more, no fewer — and
  preserve their order. If the user asks for "the whole deck", cover
  every slide.
- **Do not reproduce third-party copyrighted text** verbatim from slide
  images; paraphrase into the presenter's own spoken words.
- If you can't read the deck after a couple of attempts, say so plainly
  and ask the user to re-attach it — do not substitute placeholder slide
  content.

## Bundled helper script

`scripts/pptx_talk_track.py` uses only the Python standard library.

- `extract <deck>.pptx <slides>.json` — read slide titles, visible text,
  and existing speaker notes.
- `template <deck>.pptx <notes>.json` — write an empty notes JSON template
  with one entry per slide, ready to fill in with generated scripts.
- `apply <deck>.pptx <notes>.json <output>.pptx` — write the generated
  scripts into a copied deck as speaker notes. Never overwrites the
  original.

If a deck has no notes master, open and save it once in PowerPoint (or add
a note to one slide) before rerunning the helper.

**Runtime note:** the helper needs Python 3 available in the runtime.
Scout, Copilot Studio, and Cowork all support this, so the `extract` /
`template` / `apply` commands work on all three platforms. If the
runtime doesn't have Python for any reason, the skill still works —
paste slide text, an outline, or slide images, and the model writes
the talk track and timing table inline. In that case, users who want
the scripts embedded back into a `.pptx` as speaker notes can run the
helper locally with Python 3 installed.

## Assets and references

- `references/tone-examples.md` — short excerpts of the target
  first-person, spoken voice with delivery cues.
- `assets/example-notes.json` — example of the notes JSON shape the
  `apply` command consumes.
