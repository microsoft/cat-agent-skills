---
name: explainer-video
description: |
  Produces narrated educational explainer videos (MP4, 1080p, burned-in captions) that teach a
  concept, tool, process or policy — researching the subject where facts matter, generating office
  b-roll, and framing screenshots the user attaches. Use when the user asks to "make a video",
  "create an explainer video", "produce a training video", "a video explaining X", "turn this into
  a video", "video walkthrough", "demo video", "record a narrated overview", or asks to change a
  video this skill produced ("re-render with a longer script", "swap the b-roll"). Always writes
  the narration script and scene list and waits for approval before rendering. Do NOT use for
  slide decks with no narration or video (use pptx), for standalone images (use image-operations),
  or for audio-only podcasts (use PodcastGenerate directly).
cowork:
  category: communication
  icon: Video
---

# Explainer Video

Turns a subject under discussion into a narrated, captioned MP4 that explains it. The output is a
finished video in `output/`, not a deck and not a script.

## When NOT to Use

- **Slides for live presenting** → `pptx`. A deck is not a video.
- **A single image, diagram or infographic** → `image-operations` / `pptx`.
- **Audio only** (podcast, briefing) → call `PodcastGenerate` directly.
- **A written explainer** (SOP, guide, one-pager) → `docx`.
- **Marketing film, live action, real people's likenesses, licensed footage or music** — not
  possible here. Say so plainly and offer the b-roll style this skill can do.

## Workflow

### 1. Frame the subject (one short round)

Establish, from the conversation first and only then by asking: **subject**, **audience**
(newcomer / practitioner / exec), **target length** (default ~2 minutes ≈ 6-8 beats), and the
**angle** ("when to use each option", "how it works", "what changed"). Use `AskUserQuestion`
once — never a chain of questions.

Always ask the **visual style** in that same card: `dark` (navy slides, colour-coded sections,
photographic b-roll) or `light` (white slides, brand accents, sparing photography).

Ask whether they have **screenshots** to include if the subject is a product, tool or UI walkthrough.

### 2. Gather (only what the video actually needs)

- **Research when it matters** — external facts, product capabilities, statistics, "what's new":
  use `web_search` / `web_fetch`, or the `deep-research-agent` when claims need citing.
  Skip research entirely when the subject is already covered by this conversation or the user's
  own content. Never research a topic the user has already explained.
- **Internal subjects** — pull from `SearchM365`, `ReadFileContent`,
  meeting transcripts. Ground every internal claim in what those return.
- **Screenshots** — `Glob input/**/*` and check any `<attached_files>` block. Screenshots are used
  **as supplied**: framed, optionally box-highlighted, never regenerated or redrawn, so the product
  UI stays truthful. Note any UI text you rely on in narration so it matches the pixels.

### 3. Write the script — and STOP for approval (mandatory gate)

Build a storyboard: one **beat** per scene, each with its narration sentence(s). Rendering takes
~10-15 minutes, so the script is approved before any pixels are generated.

Show the user, inline in chat: the beat list (title + one-line narration each), the estimated
runtime (≈ 150 spoken words per minute), and the style chosen. Ask for a go-ahead or edits. Do not
generate images, audio or video until they approve.

Write the approved storyboard to `working/storyboard.json`:

```json
{
  "style": "dark",
  "beats": [
    {"kind": "title", "photo": "working/broll-wide.png", "title": "…", "sub": "…",
     "foot": "…", "narration": "…"},
    {"kind": "section", "accent": "blue", "tag": "1 / 4", "photo": "working/broll-1.png",
     "title": "…", "kicker": "…", "bullets": ["…", "…", "…"], "example": "\u201c…\u201d",
     "narration": "…"},
    {"kind": "screenshot", "accent": "green", "image": "input/shot1.png", "title": "…",
     "caption": "…", "callouts": [{"x": 40, "y": 120, "w": 400, "h": 90}], "narration": "…"},
    {"kind": "table", "photo": "working/broll-team.png", "title": "…",
     "rows": [{"left": "…", "right": "…", "accent": "blue"}], "narration": "…"},
    {"kind": "closing", "photo": "working/broll-team.png", "title": "…", "sub": "…",
     "foot": "…", "narration": "…"}
  ]
}
```

Accents: `blue`, `green`, `purple`, `orange`, `teal`, `red` — one per section, reused by its cards.

### 4. Generate the b-roll

One photo per beat that has no screenshot, via `ImageGenerate` (`quality="medium"`,
`orientation="landscape"`, `size="large"`, `destination="working"`). Issue the calls in parallel —
each takes ~2 minutes. Prompt pattern that works:

> Cinematic corporate b-roll photograph: <specific office scene with people>, modern office,
> <colour> tones, soft daylight, shallow depth of field, professional stock-photography look,
> screen content abstract and not legible, no text or logos.

Vary the scene, the people and the colour per section so the video does not repeat itself. Never
ask for real individuals, real brand logos, or legible on-screen text (the model misspells it).

### 5. Record the narration

`PodcastGenerate` with `format="single_host"` and **one turn per beat, in beat order** — the
renderer detects the pauses between turns to cut the scenes. Keep each turn conversational and
self-contained; write numbers and symbols as words. It returns the MP3 path and duration.

### 6. Compose and render

```bash
python scripts/compose_cards.py working/storyboard.json --out working/cards
python scripts/render_video.py working/storyboard.json --cards working/cards \
  --audio output/<narration>.mp3 --out working/<name>.mp4
```

`compose_cards.py` builds 1920x1080 cards (section beats get a b-roll interlude plus a detail
card). `render_video.py` aligns scene changes to the narration pauses, applies slow Ken Burns
motion to photo scenes, crossfades, generates captions from the narration and burns them in.
Rendering takes 10-15 minutes — run it with a long `initial_wait` and wait for it, never abandon
it mid-flight.

Publish the finished file:

```
CopyArtifact(surface="output", source="working/<name>.mp4", destination="<name>.mp4")
```

Then `Glob output/**/*` to confirm it landed before telling the user it is ready.

## Output Format

Deliver to `output/`: the **MP4** (1080p, H.264 + AAC, burned-in captions), plus the narration MP3
and script text that `PodcastGenerate` already writes there. In chat, state the exact
filename, the true runtime, and what each section covers — then offer the likely next edits
(different b-roll, longer script, add screenshots, a light-style version).

## Guardrails

- **The script gate is not optional.** Never generate images, audio or video before the user
  approves the beat list.
- **On-screen claims must be true of the video itself.** If a card says "a two-minute guide", the
  render must be about two minutes. Check the reported duration against every claim before
  publishing, and re-cut the card rather than shipping a mismatch.
- **Never invent facts.** Statistics, quotes, dates, product capabilities and customer names come
  from research or the user's content, or they do not appear. Where something is genuinely unknown,
  leave a visible `[placeholder]` on the card and say so — never fill it with a plausible number.
- **Screenshots are evidence, not art.** Show them as supplied. Never regenerate, retouch or
  "clean up" a product UI, and never fabricate a screenshot of a UI the user did not provide.
- **People in b-roll are synthetic and generic.** Never generate a real person's likeness, a real
  brand's logo, or copyrighted characters — offer an original equivalent instead.
- **Reproduce nothing copyrighted** in narration: no song lyrics, no verbatim article passages, no
  licensed music. Narration is original writing; quote a researched source in under 15 words with
  attribution, or paraphrase.
- **Say what failed.** If narration, image generation or the render fails after one retry, tell the
  user which part is missing rather than shipping a silent or half-built video.
