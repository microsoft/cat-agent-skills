# explainer-video — Cowork skill

Produces narrated, captioned 1080p explainer videos (MP4) that teach a concept, tool, process or
policy. Researches the subject where facts matter, generates office b-roll, frames screenshots you
supply, records a voiceover, and cuts the scenes to the narration.

## What's in the skill

```
explainer-video/
├─ SKILL.md                  the skill itself (instructions + guardrails)
└─ scripts/
   ├─ compose_cards.py       builds the 1920x1080 cards from a storyboard JSON
   └─ render_video.py        aligns scenes to the narration, adds motion, burns in captions
```

## Install

**Option A — OneDrive (easiest).** Download the skill bundle, unzip it, and copy the whole
`explainer-video` folder into your
Cowork folder in OneDrive, under `skills/`, so you end up with:

```
Documents/Cowork/skills/explainer-video/SKILL.md
Documents/Cowork/skills/explainer-video/scripts/...
```

It is available in your next Cowork session — no other setup needed.

**Option B — ask Copilot.** Attach the downloaded bundle in a Cowork chat and say
"install this skill for me".

**Sharing with a colleague:** send them the downloaded bundle and they follow Option A in their
own OneDrive. The folder name must stay `explainer-video` — it has to match the `name` inside
SKILL.md.

## Use it

Just ask for a video:

- "make a video explaining our expenses policy"
- "create an explainer video about [topic] for new starters"
- "turn this into a two-minute video walkthrough" (attach screenshots)

It asks one short round of questions (audience, length, dark or light style, screenshots), then
shows you the narration script and scene list for approval before rendering. Allow roughly 20
minutes end to end; the render itself is 10-15 of those.

## What it needs

Runs inside Cowork with no extra installation: Python with Pillow, ffmpeg, and the Copilot tools
for image generation, narration and web research. The bundled scripts are called by the skill —
you never need to run them by hand.

## Good to know

- The narration script is always approved by you before anything renders.
- Screenshots you attach are shown exactly as supplied — never redrawn or retouched.
- People in the b-roll are generated and generic; no real likenesses, logos or licensed music.
- Statistics, dates and quotes come from research or your own content, never invented.
- Alongside the MP4 you also get the narration MP3 and the script text, so you can reword and
  re-render without starting over.

Quality score at packaging time: 93/100 (Excellent).
