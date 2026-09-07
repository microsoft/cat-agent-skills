---
name: generating-podcast-script
description: Use this skill whenever the user asks to write, generate, or create a podcast script or podcast episode — from a topic, or from source material such as a news digest, newsletter, email review, or set of articles — and optionally convert it to audio with Azure Text-to-Speech. Handles the initial request and every follow-up refinement (source, topic, length, cast, narration) in the same task.
---

# Podcast Script Generation

Produces a two-host, NotebookLM-style conversational episode: a readable script
plus a multi-voice SSML document ready for Azure Text-to-Speech.

## Step 1 — Gather inputs

Ask only for what is missing. Do not ask for optional fields that have safe
defaults.

| Input | Required | Default |
|---|---|---|
| `source` or `topic` | Yes | — (source material such as a digest/newsletter/articles, **or** a plain topic) |
| `duration` | No | `medium` — `short` ≈ 3 min / ~450 words, `medium` ≈ 6 min / ~900 words, `long` ≈ 12 min / ~1,800 words |
| `language` | No | English |
| `cast` | No | Two hosts, NOVA and MILES (see Step 4) |
| `generate_audio` | No | Ask after the script is ready |

All word targets assume ~150 spoken words per minute. Stay within 10 percent of
target.

Derive a lowercase-hyphenated `<slug>` from the source or topic (max 6 words,
ASCII only).

## Step 2 — Parse the source material

Skip this step when the user gave a bare topic with no source material.

Extract every distinct article or item. For each, capture:

- headline
- publication / source
- date, if present
- the core factual claim
- any figures or quotes
- the "so what"

Merge duplicates covering the same event. Discard boilerplate, footers,
disclaimers, legal notices, unsubscribe text, and image captions.

## Step 3 — Editorial selection

Rank items by newsworthiness and reader impact. Keep the top 4 to 6 for full
treatment (fewer for `short`, more for `long`). Group the remainder into one
fast **rapid fire** segment. If the material has a dominant theme, lead with it
and thread it through the episode.

## Step 4 — Cast

Two hosts, always the same personalities, always distinct voices:

- **NOVA** — voice `en-US-AvaMultilingualNeural`. Lead host. Warm, curious,
  quick. Drives the agenda, asks the question the listener is thinking, reacts
  out loud, reframes jargon into plain language. Slightly faster cadence.
- **MILES** — voice `en-US-AndrewMultilingualNeural`. Analyst. Calm, dry,
  precise. Supplies context, numbers, caveats, second-order implications.
  Slightly slower, lower pitch. Occasionally pushes back on Nova.

Neither host is a narrator. They talk **to each other**, not to the microphone.

## Step 5 — Episode structure

1. **Cold open** (15–20s) — Nova opens on the single most striking fact or
   tension. No "welcome to the podcast", no channel branding, no music cues.
2. **Agenda tease** (10s) — Miles lays out what they'll cover, casually.
3. **Story segments** (60–90s each) — one item per segment. Pattern:
   hook → the facts → why it matters → a short exchange of interpretation →
   handoff line into the next story. Vary who leads each segment.
4. **Rapid fire** (45s) — alternating one-liners on the leftover items, quick
   tempo.
5. **Close** (20–30s) — three concrete takeaways split between the two hosts,
   then a short human sign-off. Alternate whether Nova or Miles ends.

## Step 6 — Dialogue style

This is what makes it sound conversational rather than read-aloud.

- Write spoken English, not written English. Contractions everywhere.
- Keep most lines under 30 words. Break long explanations across two or three
  turns with the other host interjecting.
- Use real conversational connective tissue — "okay so", "right", "wait, back
  up", "here's the part I didn't expect", "yeah, and that's the thing", "hmm".
  Roughly one marker every 4 to 5 turns. Never let it become a tic.
- One host regularly asks the naive clarifying question so the other can
  explain.
- Use one concrete analogy or comparison per complex item.
- Genuine reactions are allowed ("that number is wild"). Invented opinions on
  people, companies, or politics are not.
- Never read a headline verbatim. Paraphrase it into speech.
- Attribute clearly: "according to the Financial Times", "Reuters is
  reporting".
- If the source is ambiguous or a claim is unconfirmed, say so on air: "the
  report is careful to call that unconfirmed".
- No stage directions, no "[laughs]", no speaker labels, no markdown, no
  emojis, no bullet points, and no URLs in the **spoken text**.

## Step 7 — TTS hygiene

Applies to every word that will be spoken.

- Spell out anything a synthesizer would mangle: "twenty twenty-six" not
  `2026`, "three point two billion dollars" not `$3.2B`, "about fifteen
  percent" not `~15%`.
- First mention of an acronym: expand it, then use the short form.
- Letter-by-letter acronyms: `<say-as interpret-as="characters">API</say-as>`.
- Odd proper nouns: `<sub alias="phonetic spelling">Name</sub>`.
- A non-English name or phrase inside an English line:
  `<lang xml:lang="fr-FR">...</lang>`.
- Escape XML entities in all spoken text: `&` → `&amp;`, `<` → `&lt;`,
  `>` → `&gt;`.
- Never emit smart quotes, em dashes, asterisks, or underscores.

## Step 8 — Write the readable script

Write the human-readable transcript to:

```text
/app/created/<slug>_Podcast_Script.txt
```

This file — and only this file — may carry `NOVA:` / `MILES:` speaker labels so
a person can follow along. It contains no stage directions and no markdown. The
spoken text itself must already satisfy Steps 6 and 7 so it can be lifted into
SSML unchanged.

## Step 9 — SSML output contract

Produce the SSML document and **nothing else** — no preamble, no explanation, no
code fences, no trailing notes inside the artifact. Write it verbatim to:

```text
/app/created/<slug>_Podcast.ssml
```

Rules:

- Exactly one root `<speak>` element with `version="1.0"`,
  `xmlns="http://www.w3.org/2001/10/synthesis"`,
  `xmlns:mstts="http://www.w3.org/2001/mstts"`, `xml:lang="en-US"`.
- One `<voice>` element per conversational turn. Alternate speakers. Never put
  both hosts inside one `<voice>` element.
- Vary delivery with `<prosody>` so it never sounds flat. Baselines: Nova
  `rate="+6%" pitch="+2%"`, Miles `rate="-2%" pitch="-4%"`. Nudge per line to
  match the emotion of the sentence.
- Use `<mstts:express-as style="...">` where the voice supports it. Preferred
  styles: `chat` for banter, `friendly` for explanation,
  `narration-professional` for the factual core of a story, `excited` sparingly
  for the cold open. An unsupported style is ignored by the service, so keep
  styles optional — never structural.
- Pauses: `<break time="250ms"/>` between turns within a segment,
  `<break time="700ms"/>` between segments, `<break time="400ms"/>` before a
  punchline or a pivot. Never exceed `900ms`.
- **Every `<break>` must sit inside a `<voice>` element.** A `<break>` placed
  between `<voice>` elements — as a direct child of `<speak>` — is invalid in a
  multi-voice document and will fail synthesis. Two `<voice>` elements may sit
  directly next to each other with nothing between them. To pause *between*
  turns, put the break at the **end of the preceding turn's** text, inside that
  turn's `<prosody>`.
- `<emphasis level="moderate">` on at most one or two key terms per segment.
- Keep the total document under 40,000 characters.

### Shape

```xml
<speak version="1.0"
       xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts"
       xml:lang="en-US">
  <voice name="en-US-AvaMultilingualNeural">
    <mstts:express-as style="excited">
      <prosody rate="+8%" pitch="+3%">Okay, so the number that stopped me cold
      this morning was forty percent. <break time="300ms"/> Forty percent, in one
      quarter. <break time="250ms"/></prosody>
    </mstts:express-as>
  </voice>
  <voice name="en-US-AndrewMultilingualNeural">
    <mstts:express-as style="chat">
      <prosody rate="-2%" pitch="-4%">Right, and the part everyone's skipping is
      that it's off a very small base. <break time="250ms"/> Context matters
      here. <break time="700ms"/></prosody>
    </mstts:express-as>
  </voice>
</speak>
```

Note the trailing `<break>` closing each turn: the 250ms is the gap before the
next turn, the 700ms is the longer gap before the next segment. Nothing sits
between the two `<voice>` elements.

## Step 10 — Review, then generate audio

Show the user a table summarising each segment (title, one-line description,
approximate spoken duration), print both file paths, and ask:

> Would you like me to convert this to an audio file?

Only if they say yes:

1. Confirm the `ConverttexttospeechwithSSML` tool is available on the agent. If
   it is not, tell the user how to add it and stop.
2. Call `ConverttexttospeechwithSSML` with the SSML document from Step 9 and
   `outputFormat: riff-24khz-16bit-mono-pcm`.
3. Decode the base64 response and save to `/app/created/<slug>_Podcast.wav`.

If the document is too large for a single call, split it at a segment boundary and synthesize each part separately.
When stitching, do NOT concatenate decoded RIFF/WAV bytes; instead, append the audio at the PCM-frame level (e.g., via Python’s `wave` module) and write a single valid `/app/created/<slug>_Podcast.wav` with one header.

```python
import base64

with open('<tool_output_file>', 'r') as f:
    content = f.read().strip()

audio_bytes = base64.b64decode(content)

with open('/app/created/<slug>_Podcast.wav', 'wb') as f:
    f.write(audio_bytes)
```

## Step 11 — Final report

Always end with:

| Item | Details |
|---|---|
| Script file | `/app/created/<slug>_Podcast_Script.txt` |
| SSML file | `/app/created/<slug>_Podcast.ssml` |
| Word count / estimated duration | actual vs. target at ~150 wpm |
| Items covered | full segments + rapid-fire count |
| Voices | `en-US-AvaMultilingualNeural` (Nova), `en-US-AndrewMultilingualNeural` (Miles) |
| Audio file | `/app/created/<slug>_Podcast.wav` *(only if audio generated)* |
